package data

import (
	"cmp"
	"dpd/go_modules/dpdDb"
	"dpd/go_modules/tools"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"sync"
	"time"
)

var M = InitMatchData()

var Mu = sync.Mutex{}
var TestWord = ""
var BlockedTries = 0
var MaxedOut = 0

var pf = fmt.Printf
var pl = fmt.Println
var spf = fmt.Sprintf

// TODO update
// The MatchData is used globally and stores:
//  1. a list of match items
//  2. a list of matches strings for quick lookup
type MatchData struct {
	MatchedItems []MatchItem         // list of matchItems
	MatchedMap   map[string][]string // word : list of matches
	TriedMap     map[string][]string // has the word.front + middle + back been tried already?
	Unmatched    map[string]string   // unmatched words remaining
	StartTime    time.Time           // global start time
	ProcessCount map[string]int      // how many processes has the word gone through in total
	WordStats    []statistics        //	word stats
	TopFive      map[string][]string //	top five entries for export
}

func InitMatchData() MatchData {
	var m = MatchData{}
	m.MatchedMap = map[string][]string{}
	m.TriedMap = map[string][]string{}
	m.StartTime = time.Now()
	m.ProcessCount = map[string]int{}
	m.WordStats = []statistics{}
	return m
}

// Lookup the word in m.matchedMap
// and if it exists, return the opposite.
func (m MatchData) HasNoMatches(w WordData) bool {
	Mu.Lock()
	_, exists := m.MatchedMap[string(w.Word)]
	Mu.Unlock()
	return !exists

}

// Has this word already been tried? If not, add to the triedMap.
func (m *MatchData) NotTriedYet(w WordData) bool {
	splitString := w.MakeSplitString()
	Mu.Lock()
	splitList := m.TriedMap[string(w.Word)]
	Mu.Unlock()
	if slices.Contains(splitList, splitString) {
		return false
	} else {
		Mu.Lock()
		m.TriedMap[string(w.Word)] = append(splitList, splitString)
		Mu.Unlock()
		return true
	}

}

func (m MatchData) matchCount(w WordData) int {
	Mu.Lock()
	list := m.MatchedMap[string(w.Word)]
	Mu.Unlock()
	return len(list)
}

func (m MatchData) ProcessCounter(w WordData) int {
	Mu.Lock()
	processes := m.ProcessCount[string(w.Word)]
	Mu.Unlock()
	return processes
}

func (m *MatchData) ProcessPlusOne(w WordData) {
	Mu.Lock()
	m.ProcessCount[string(w.Word)] = m.ProcessCount[string(w.Word)] + 1
	Mu.Unlock()
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

	Mu.Lock()
	shouldAdd := !slices.Contains(
		m.MatchedMap[string(w.Word)], splitString)
	Mu.Unlock()

	if shouldAdd {
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

		Mu.Lock()
		m.MatchedItems = append(m.MatchedItems, mi)
		m.MatchedMap[string(w.Word)] = append(m.MatchedMap[string(w.Word)], splitString)
		delete(m.Unmatched, string(w.Word))
		Mu.Unlock()
	}
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

func processMatched() (float64, float64, MatchItem) {

	var timeLongest float64
	var timeTotal float64
	var slowestWord MatchItem

	for _, mi := range M.MatchedItems {
		// if mi.Word == TestWord {
		// 	pf("%v, %v, %q, %v, %v, %f\n",
		// 		i, mi.Word, mi.Split, mi.FinalProcess, mi.Route, mi.Time)
		// }
		// if testWord == "" {
		// 	pf("%v, %v, %q, %v, %v, %f\n",
		// 		i, mi.word, mi.split, mi.finalProcess, mi.route, mi.time)
		// }
		timeTotal = timeTotal + mi.Time
		if mi.Time > timeLongest {
			timeLongest = mi.Time
			slowestWord = mi
		}
	}
	return timeLongest, timeTotal, slowestWord
}

func (m *MatchData) Summary() {

	MTimeLongest, MTimeTotal, MSlowestWord := processMatched()

	// Sort by
	//  1. alphabetical order
	//  2. ProcessCount
	//  3. weight

	slices.SortFunc(m.MatchedItems, func(a, b MatchItem) int {
		if n := cmp.Compare(a.Word, b.Word); n != 0 {
			return n
		} else if n := cmp.Compare(a.ProcessCount, b.ProcessCount); n != 0 {
			return n
		} else if n := cmp.Compare(a.Weight, b.Weight); n != 0 {
			return n
		} else {
			return cmp.Compare(a.SplitRatio, b.SplitRatio)
		}
	})

	matchItemsLen := len(m.MatchedItems)
	initial := len(G.Unmatched)
	matched := len(G.Unmatched) - len(m.Unmatched)
	unmatched := len(m.Unmatched)
	averMatches := float64(matchItemsLen) / float64(matched)
	matchedPrc := (float64(matched) / float64(initial)) * 100
	unmatchedPrc := (float64(unmatched) / float64(initial)) * 100
	MTimeAverage := MTimeTotal / float64(matchItemsLen)
	timeInSec := time.Since(m.StartTime).Seconds()
	timeInMin := time.Since(m.StartTime).Minutes()

	pf("blocked tries:		%d\n", BlockedTries)
	pf("maxed out:		%d\n", MaxedOut)
	pl()
	pf("initial words:		%d\n", initial)
	pf("words matched:     	%d\n", matched)
	pf("words unmatched:	%d\n", unmatched)
	pf("match items:		%d\n", matchItemsLen)
	pf("average matches:	%.3f\n", averMatches)
	pf("matched %%:		%f %%\n", matchedPrc)
	pf("unmatched %%:		%f %%\n", unmatchedPrc)
	pl()
	pf("match longest time:	%.3f sec\n", MTimeLongest)
	pf("match average time:	%.3f sec\n", MTimeAverage)
	pf("match slowest word:	%v\n", MSlowestWord.Word)
	pf("total seconds:		%.3f sec\n", timeInSec)
	pf("total minutes:		%.3f min\n", timeInMin)
	pl()

}

func (m MatchData) SaveMatchedTsv() {
	pf("saving matches:		")

	filePath := filepath.Join(tools.Pth.DpdBaseDir, tools.Pth.MatchesTsv)
	separator := "\t"
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
	data := [][]string{}
	for _, mi := range m.MatchedItems {
		row := []string{
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
		}
		data = append(data, row)
	}
	tools.SaveTsv(filePath, separator, header, data)
	fileInfo, _ := os.Stat(filePath)
	pf("%v rows, %.1fMB\n", len(data), float64(fileInfo.Size())/1000/1000)

}

type unMatchedItem struct {
	word    string
	CstFreq int
	BjtFreq int
	SyaFreq int
	ScFreq  int
}

func (m MatchData) SaveUnmatchedTsv() {
	pf("saving unmatched:	")

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
	pf("%v rows, %.1fMB\n", len(data), float64(fileInfo.Size())/1000/1000)
}

func (m MatchData) SaveTopEntriesJson() {
	pf("making top %v json:	", L.TopDictLimit)

	topDict := map[string][]string{}   // top five entries
	processCounter := map[string]int{} // process counter
	extraCounter := map[string]int{}   // extra word counter

	for _, mi := range m.MatchedItems {
		// TODO add to learn_go
		entryList, exists := topDict[mi.Word]
		entry := spf("%v", mi.Split)

		if !exists {
			topDict[mi.Word] = append(entryList, entry)
			processCounter[mi.Word] = mi.ProcessCount // PC = Process Count

		} else {
			if slices.Contains(entryList, entry) {
				pf("! error ! %v already in list", entry)

			} else {
				// limit the Dictionary entries
				if len(entryList) < L.TopDictLimit {
					if mi.ProcessCount <= processCounter[mi.Word]+1 { // only allow words with 1 or 2 more ProcessCount
						if extraCounter[mi.Word] < 2 { // only allow two more
							topDict[mi.Word] = append(entryList, entry)
						}
						if mi.ProcessCount > processCounter[mi.Word] {
							extraCounter[mi.Word] = extraCounter[mi.Word] + 1
						}
					}
				}
			}
		}
	}

	M.TopFive = topDict

	filePath := tools.Pth.DeconstructorOutput
	tools.SaveJson(filePath, topDict)
	fileInfo, _ := os.Stat(filePath)
	pf("%v rows, %.1fMB\n", len(topDict), float64(fileInfo.Size())/1000/1000)
}

// get the lookup db
// for each entry add update or delete

func (m MatchData) SaveToDb() {
	pl()
	pl("saving to db")
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

	pf("added: 			%v\n", addedCount)
	pf("updated: 		%v\n", updatedCount)
	pf("deleted: 		%v\n", deletedCount)
	pf("muted: 			%v\n", mutedCount)
	pf("db time: 		%v\n", time.Since(saveTime).Seconds())
	pf("total time:		%v\n", time.Since(m.StartTime).Seconds())
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
