package data

import (
	"cmp"
	"dpd/go_modules/dpdDb"
	"dpd/go_modules/tools"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"sync/atomic"
	"time"
)

var M = InitMatchData()

var TestWord = ""
var BlockedTries atomic.Int64
var MaxedOut atomic.Int64

// FinishWordDupes counts words flushed more than once per worker. With
// per-worker word contiguity (each word is produced by exactly one worker in a
// single deconstruct call) this stays 0; a non-zero value means the streaming
// selection saw a word out of contiguity and the output may diverge from the
// golden.
var FinishWordDupes atomic.Int64

var spf = fmt.Sprintf

// MatchData is a per-worker accumulator. Each worker owns one and touches it
// single-threaded, so no locking is needed on the hot path.
//
// Match rows are no longer kept in one big in-RAM slice. Instead each candidate
// is streamed to the worker's own file (for matches.tsv) and the per-word top-5
// selection is done inline as each word finishes, keeping only one word's
// candidates in RAM at a time. The per-word maps are cleared between words so no
// large map accumulates across a worker's ~20k words.
type MatchData struct {
	file     *os.File    // this worker's streamed match rows
	csvw     *csv.Writer // tab-separated writer over file
	FilePath string      // path of file, for concatenation into matches.tsv

	wordBuf []MatchItem         // candidates for the word currently being processed
	topDict map[string][]string // per-worker top-5 selections, keyed by word

	MatchedMap   map[string][]string // word : list of matches (current word only)
	TriedMap     map[string][]string // tried split strings (current word only)
	ProcessCount map[string]int      // total processes per word (current word only)

	itemCount   int     // total candidate rows produced by this worker
	timeLongest float64 // slowest single match time
	timeTotal   float64 // sum of match times
	slowestWord string  // word of the slowest match

	WordStats []statistics // per-word stats

	// Fields below are only used on the global M after merging.
	Unmatched         map[string]string   // unmatched words remaining
	ManualCorrections []MatchItem         // manual corrections, seeded before compute
	StartTime         time.Time           // global start time
	TopFive           map[string][]string // top five entries for export
}

func InitMatchData() MatchData {
	var m = MatchData{}
	m.topDict = map[string][]string{}
	m.MatchedMap = map[string][]string{}
	m.TriedMap = map[string][]string{}
	m.ProcessCount = map[string]int{}
	m.StartTime = time.Now()
	m.WordStats = []statistics{}
	return m
}

// NewMatchData returns a fresh in-memory per-worker accumulator with no backing
// file. Used by tests; production/bench use NewWorkerFactory.
func NewMatchData() *MatchData {
	m := InitMatchData()
	return &m
}

// NewWorkerFactory returns a function that builds one per-worker MatchData
// backed by its own file in dir. RunCollect calls it once per worker in the main
// goroutine (sequentially), so the plain counter needs no locking.
func NewWorkerFactory(dir string) func() *MatchData {
	var counter int
	return func() *MatchData {
		m := InitMatchData()
		path := filepath.Join(dir, spf("matches_%d.tsv", counter))
		counter++
		f, err := os.Create(path)
		tools.HardCheck(err)
		m.file = f
		m.FilePath = path
		m.csvw = csv.NewWriter(f)
		m.csvw.Comma = '\t'
		return &m
	}
}

// ResetWord clears the per-word maps at the start of each word's processing.
// Every access to these maps is keyed by the word currently in deconstruct, so
// clearing between words is behaviour-preserving and keeps memory flat.
func (m *MatchData) ResetWord() {
	clear(m.MatchedMap)
	clear(m.TriedMap)
	clear(m.ProcessCount)
}

// FinishWord selects the top-5 for the word(s) in wordBuf and clears it. Called
// once per deconstruct, after all of a word's candidates have been produced.
func (m *MatchData) FinishWord() {
	if len(m.wordBuf) == 0 {
		return
	}

	// Sort the buffer so each word's candidates form a contiguous, correctly
	// ordered block (normally the buffer holds a single word).
	slices.SortFunc(m.wordBuf, compareMatchItems)

	start := 0
	for i := 1; i <= len(m.wordBuf); i++ {
		if i == len(m.wordBuf) || m.wordBuf[i].Word != m.wordBuf[start].Word {
			word := m.wordBuf[start].Word
			if _, exists := m.topDict[word]; exists {
				FinishWordDupes.Add(1)
			}
			m.topDict[word] = selectTopEntries(m.wordBuf[start:i], L.TopDictLimit)
			start = i
		}
	}

	m.wordBuf = m.wordBuf[:0]
}

// CloseWorkers flushes and closes every worker's streamed file.
func CloseWorkers(workers []*MatchData) {
	for _, w := range workers {
		if w == nil || w.csvw == nil {
			continue
		}
		w.csvw.Flush()
		tools.HardCheck(w.csvw.Error())
		tools.HardCheck(w.file.Close())
	}
}

// CleanupWorkers removes every worker's temp file.
func CleanupWorkers(workers []*MatchData) {
	for _, w := range workers {
		if w == nil || w.FilePath == "" {
			continue
		}
		os.Remove(w.FilePath)
	}
}

// Merge folds the per-worker accumulators into the global M: it unions the
// worker top-5 dicts, overlays the manual corrections, marks matched words, and
// aggregates the summary counters and per-word stats. Words are produced by
// exactly one worker (verified: 0 cross-worker words on a full corpus), so the
// top-dict union is a disjoint merge.
func (m *MatchData) Merge(parts []*MatchData) {
	topDict := map[string][]string{}

	// Manual corrections first: their words are excluded from the deconstructor
	// input, so they never collide with a worker's words. Group by word and run
	// the same selection rule so each word's list is built identically.
	manualByWord := map[string][]MatchItem{}
	order := []string{}
	for _, mi := range m.ManualCorrections {
		if _, seen := manualByWord[mi.Word]; !seen {
			order = append(order, mi.Word)
		}
		manualByWord[mi.Word] = append(manualByWord[mi.Word], mi)
	}
	for _, word := range order {
		items := manualByWord[word]
		slices.SortFunc(items, compareMatchItems)
		topDict[word] = selectTopEntries(items, L.TopDictLimit)
		delete(m.Unmatched, word)
	}

	for _, p := range parts {
		if p == nil {
			continue
		}
		for word, entries := range p.topDict {
			if _, exists := topDict[word]; exists {
				FinishWordDupes.Add(1)
			}
			topDict[word] = entries
			delete(m.Unmatched, word)
		}
		m.WordStats = append(m.WordStats, p.WordStats...)
		m.itemCount += p.itemCount
		m.timeTotal += p.timeTotal
		if p.timeLongest > m.timeLongest {
			m.timeLongest = p.timeLongest
			m.slowestWord = p.slowestWord
		}
	}

	m.itemCount += len(m.ManualCorrections)
	m.TopFive = topDict
}

// Lookup the word in m.MatchedMap and if it exists, return the opposite.
func (m *MatchData) HasNoMatches(w WordData) bool {
	_, exists := m.MatchedMap[string(w.Word)]
	return !exists
}

// Has this word already been tried? If not, add to the triedMap.
func (m *MatchData) NotTriedYet(w WordData) bool {
	splitString := w.MakeSplitString()
	splitList := m.TriedMap[string(w.Word)]
	if slices.Contains(splitList, splitString) {
		return false
	}
	m.TriedMap[string(w.Word)] = append(splitList, splitString)
	return true
}

func (m *MatchData) ProcessCounter(w WordData) int {
	return m.ProcessCount[string(w.Word)]
}

func (m *MatchData) ProcessPlusOne(w WordData) {
	m.ProcessCount[string(w.Word)] = m.ProcessCount[string(w.Word)] + 1
}

// single match datum
type MatchItem struct {
	Word         string  // the word in a text
	Split        string  // word split using " + "
	SplitCount   int     // number of splits
	SplitRatio   float64 // ratio of (split : word) length
	Route        string  // which processes have been applied to create the splits
	FinalProcess string  // the last process
	Rules        string  // which rules have been applied to create the splits
	Weight       float64 // sum of the weights of each split divided by ProcessCount
	ProcessCount int     // number of process to create the split
	Time         float64 // time taken to create the split
}

func (m *MatchData) MakeMatch(
	processName string,
	w WordData) {

	splitString, splitCount, splitRatio := compileMatchData(w)

	if slices.Contains(m.MatchedMap[string(w.Word)], splitString) {
		return
	}

	mi := MatchItem{}
	mi.Word = string(w.Word)
	mi.Split = splitString
	mi.SplitCount = splitCount
	mi.SplitRatio = splitRatio
	mi.FinalProcess = processName
	mi.Route = w.pathString()
	mi.Rules = w.ruleString()
	mi.Weight = float64(w.Weight) / float64(w.ProcessCount)
	mi.ProcessCount = w.ProcessCount
	mi.Time = float64(time.Since(w.StartTime).Seconds())

	m.wordBuf = append(m.wordBuf, mi)
	m.MatchedMap[string(w.Word)] = append(m.MatchedMap[string(w.Word)], splitString)

	m.writeRow(mi)

	m.itemCount++
	m.timeTotal += mi.Time
	if mi.Time > m.timeLongest {
		m.timeLongest = mi.Time
		m.slowestWord = mi.Word
	}
}

// writeRow streams a single candidate to the worker's file, in the same column
// order as matches.tsv.
func (m *MatchData) writeRow(mi MatchItem) {
	if m.csvw == nil {
		return
	}
	err := m.csvw.Write([]string{
		mi.Word,
		mi.Split,
		tools.Int2Str(mi.SplitCount),
		tools.Float2Str(mi.SplitRatio),
		tools.Float2Str(mi.Weight),
		tools.Int2Str(mi.ProcessCount),
		mi.Rules,
		mi.Route,
		mi.FinalProcess,
		tools.Float2Str(mi.Time),
	})
	tools.HardCheck(err)
}

// compareMatchItems is the total-order ranking used for the top-5 selection.
// Sort by
//  1. alphabetical order
//  2. ProcessCount
//  3. weight
//  4. split ratio
//  5. split text (final tiebreak → total order → deterministic output)
func compareMatchItems(a, b MatchItem) int {
	if n := cmp.Compare(a.Word, b.Word); n != 0 {
		return n
	} else if n := cmp.Compare(a.ProcessCount, b.ProcessCount); n != 0 {
		return n
	} else if n := cmp.Compare(a.Weight, b.Weight); n != 0 {
		return n
	} else if n := cmp.Compare(a.SplitRatio, b.SplitRatio); n != 0 {
		return n
	} else {
		return cmp.Compare(a.Split, b.Split)
	}
}

// selectTopEntries applies the top-N selection rule to one word's candidates,
// which must already be sorted by compareMatchItems. It reproduces the original
// global SaveTopEntriesJson logic per word: the first (lowest-ProcessCount)
// candidate is always kept, and further candidates are kept only while the list
// is under the limit and their ProcessCount does not exceed the first's.
func selectTopEntries(items []MatchItem, limit int) []string {
	out := []string{}
	var processCounter int
	extraCounter := 0

	for i, mi := range items {
		if i == 0 {
			out = append(out, mi.Split)
			processCounter = mi.ProcessCount
			continue
		}
		if slices.Contains(out, mi.Split) {
			continue
		}
		if len(out) < limit {
			if mi.ProcessCount <= processCounter {
				if extraCounter < 2 {
					out = append(out, mi.Split)
				}
				if mi.ProcessCount > processCounter {
					extraCounter++
				}
			}
		}
	}
	return out
}

// TODO update
// A function that takes a w structs.WordData and the middle words
// compiles to list of string and joins with " + "
func compileMatchData(w WordData) (string, int, float64) {
	splitList := []string{}

	for _, slice := range w.Front {
		splitList = append(splitList, string(slice))
	}

	splitList = append(splitList, string(w.Middle))

	for _, slice := range w.Back {
		splitList = append(splitList, string(slice))
	}
	splitString := strings.Join(splitList, " + ")
	splitCount := strings.Count(splitString, " + ")

	splitStringRaw := strings.Join(splitList, "")
	splitRatio := float64(tools.StrLen(splitStringRaw)) / float64((len(w.Word)))

	return splitString, splitCount, splitRatio
}

func (m *MatchData) Summary() {

	// Sort by
	//  1. alphabetical order
	//  2. ProcessCount
	//  3. weight

	matchItemsLen := m.itemCount
	initial := len(G.Unmatched)
	matched := len(G.Unmatched) - len(m.Unmatched)
	unmatched := len(m.Unmatched)
	averMatches := float64(matchItemsLen) / float64(matched)
	matchedPrc := (float64(matched) / float64(initial)) * 100
	unmatchedPrc := (float64(unmatched) / float64(initial)) * 100
	MTimeAverage := m.timeTotal / float64(matchItemsLen)
	timeInSec := time.Since(m.StartTime).Seconds()
	timeInMin := time.Since(m.StartTime).Minutes()

	tools.PTitle("Summary")
	tools.PGreen("blocked tries:")
	tools.POk(fmt.Sprintf("%d", BlockedTries.Load()))
	tools.PGreen("maxed out:")
	tools.POk(fmt.Sprintf("%d", MaxedOut.Load()))
	tools.PGreen("finish-word dupes:")
	tools.POk(fmt.Sprintf("%d", FinishWordDupes.Load()))
	tools.POk("")
	tools.PGreen("initial words:")
	tools.POk(fmt.Sprintf("%d", initial))
	tools.PGreen("words matched:")
	tools.POk(fmt.Sprintf("%d", matched))
	tools.PGreen("words unmatched:")
	tools.POk(fmt.Sprintf("%d", unmatched))
	tools.PGreen("match items:")
	tools.POk(fmt.Sprintf("%d", matchItemsLen))
	tools.PGreen("average matches:")
	tools.POk(fmt.Sprintf("%.3f", averMatches))
	tools.PGreen("matched %%:")
	tools.POk(fmt.Sprintf("%.6f %%", matchedPrc))
	tools.PGreen("unmatched %%:")
	tools.POk(fmt.Sprintf("%.6f %%", unmatchedPrc))
	tools.POk("")
	tools.PGreen("match longest time:")
	tools.POk(fmt.Sprintf("%.3f sec", m.timeLongest))
	tools.PGreen("match average time:")
	tools.POk(fmt.Sprintf("%.3f sec", MTimeAverage))
	tools.PGreen("match slowest word:")
	tools.POk(m.slowestWord)
	tools.PGreen("total seconds:")
	tools.POk(fmt.Sprintf("%.3f sec", timeInSec))
	tools.PGreen("total minutes:")
	tools.POk(fmt.Sprintf("%.3f min", timeInMin))
	tools.POk("")

}

// SaveMatchedTsv writes matches.tsv as the header followed by the concatenation
// of every worker's streamed file (all candidates preserved). Row order is
// production order, not globally sorted — matches.tsv is a debug artifact, not
// the correctness target.
func (m MatchData) SaveMatchedTsv(workers []*MatchData) {
	tools.PGreen("saving matches:")

	filePath := filepath.Join(tools.Pth.DpdBaseDir, tools.Pth.MatchesTsv)
	out, err := os.Create(filePath)
	tools.HardCheck(err)

	w := csv.NewWriter(out)
	w.Comma = '\t'
	header := []string{
		"word",
		"split",
		"split_count",
		"split_ratio",
		"weight",
		"process_count",
		"rules",
		"route",
		"final_process",
		"time",
	}
	tools.HardCheck(w.Write(header))
	w.Flush()
	tools.HardCheck(w.Error())

	for _, wkr := range workers {
		if wkr == nil || wkr.FilePath == "" {
			continue
		}
		in, err := os.Open(wkr.FilePath)
		tools.HardCheck(err)
		_, err = io.Copy(out, in)
		tools.HardCheck(err)
		tools.HardCheck(in.Close())
	}
	tools.HardCheck(out.Close())

	fileInfo, _ := os.Stat(filePath)
	tools.POk(fmt.Sprintf("%v rows, %.1fMB", m.itemCount, float64(fileInfo.Size())/1000/1000))
}

type unMatchedItem struct {
	word    string
	CstFreq int
	BjtFreq int
	SyaFreq int
	ScFreq  int
}

func (m MatchData) SaveUnmatchedTsv() {
	tools.PGreen("saving unmatched:")

	// make a list of unmatchedItems to sort
	cstFreqMap := tools.LoadCstFreqMap()
	bjtFreqMap := tools.LoadBjtFreqMap()
	syaFreqMap := tools.LoadSyaFreqMap()
	scFreqMap := tools.LoadScFreqMap()

	unmatchedList := []unMatchedItem{}
	for word := range m.Unmatched {
		ui := unMatchedItem{}
		ui.word = word
		ui.CstFreq = cstFreqMap[word]
		ui.BjtFreq = bjtFreqMap[word]
		ui.SyaFreq = syaFreqMap[word]
		ui.ScFreq = scFreqMap[word]
		unmatchedList = append(unmatchedList, ui)
	}
	slices.SortFunc(unmatchedList, func(a, b unMatchedItem) int {
		return cmp.Compare(b.CstFreq, a.CstFreq)
	})

	// save to tsv
	filePath := tools.Pth.UnMatchedTsv
	separator := "\t"
	header := []string{"unmatched", "cst", "bjt", "sya", "sc"}

	data := [][]string{}
	for _, i := range unmatchedList {
		data = append(
			data,
			[]string{
				i.word,
				tools.Int2Str(i.CstFreq),
				tools.Int2Str(i.BjtFreq),
				tools.Int2Str(i.SyaFreq),
				tools.Int2Str(i.ScFreq),
			},
		)
	}

	tools.SaveTsv(filePath, separator, header, data)
	fileInfo, _ := os.Stat(filePath)
	tools.POk(fmt.Sprintf("%v rows, %.1fMB", len(data), float64(fileInfo.Size())/1000/1000))
}

func (m MatchData) SaveTopEntriesJson() {
	tools.PGreen(fmt.Sprintf("making top %v json:", L.TopDictLimit))

	filePath := tools.Pth.DeconstructorOutput
	tools.SaveJson(filePath, m.TopFive)
	fileInfo, _ := os.Stat(filePath)
	tools.POk(fmt.Sprintf("%v rows, %.1fMB", len(m.TopFive), float64(fileInfo.Size())/1000/1000))
}

// get the lookup db
// for each entry add update or delete

func (m MatchData) SaveToDb() {
	tools.PTitle("Saving to DB")
	db, results := dpdDb.GetLookup()

	// iterate through results
	// if in lookup key & in top five: update
	// if in lookup key & not in top five & has other values: mute
	// if in lookup key & not in top five & has no other values: delete
	// if not in lookup key and in top five, add

	addedCount := 0
	updatedCount := 0
	deletedCount := 0
	mutedCount := 0

	saveTime := time.Now()
	lookupKeys := map[string]string{} // collect the keys
	updatedResults := []dpdDb.Lookup{}

	// updated, delete, mute
	for _, l := range results {
		// if i%10000 == 0 {
		// 	pf("%v / %v %v\n", i, len(results), l.Key)
		// }
		lookupKeys[l.Key] = ""
		_, exists := m.TopFive[l.Key]
		if exists {
			jsonData, err := json.Marshal(m.TopFive[l.Key])
			tools.HardCheck(err)
			l.Deconstructor = string(jsonData)
			updatedResults = append(updatedResults, l)
			updatedCount++
		} else {
			if shouldDelete(l) {
				// don't add it to the updatedResults, that's all
				deletedCount++
			} else {
				l.Deconstructor = ""
				updatedResults = append(updatedResults, l)
				mutedCount++
			}
		}
	}

	// what needs to be added?
	for key, value := range m.TopFive {
		_, exists := lookupKeys[key]
		if !exists {
			l := dpdDb.Lookup{}
			l.Key = key
			jsonData, err := json.Marshal(value)
			tools.HardCheck(err)
			l.Deconstructor = string(jsonData)
			updatedResults = append(updatedResults, l)
			addedCount++
		}
	}

	tx := db.Begin()
	// defer dpdDb.Rollback(tx)

	// wipe the table clean
	tx.Exec("DELETE FROM lookup")

	// add the updated rows
	tx.CreateInBatches(updatedResults, 2000)
	tx.Commit()

	tools.PGreen("added:")
	tools.POk(fmt.Sprintf("%v", addedCount))
	tools.PGreen("updated:")
	tools.POk(fmt.Sprintf("%v", updatedCount))
	tools.PGreen("deleted:")
	tools.POk(fmt.Sprintf("%v", deletedCount))
	tools.PGreen("muted:")
	tools.POk(fmt.Sprintf("%v", mutedCount))
	tools.PGreen("db time:")
	tools.POk(fmt.Sprintf("%v", time.Since(saveTime).Seconds()))
	tools.PGreen("total time:")
	tools.POk(fmt.Sprintf("%v", time.Since(m.StartTime).Seconds()))
}

func shouldDelete(l dpdDb.Lookup) bool {
	// TODO surely this can be automated
	if l.Headwords != "" {
		return false
	}
	if l.Roots != "" {
		return false
	}
	if l.Variant != "" {
		return false
	}
	if l.Spelling != "" {
		return false
	}
	if l.Grammar != "" {
		return false
	}
	if l.Help != "" {
		return false
	}
	if l.Abbrev != "" {
		return false
	}
	if l.Epd != "" {
		return false
	}
	if l.Rpd != "" {
		return false
	}
	return true
}
