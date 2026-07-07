package main

import (
	"bytes"
	"dpd/go_modules/deconstructor/workerpool"
	"dpd/go_modules/dpdDb"
	"dpd/go_modules/frequency/gradient"
	"dpd/go_modules/tools"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"slices"
	"strings"
	"sync"
	"text/template"

	"gorm.io/gorm"
)

var tic = tools.Tic()

// corpus holds one edition's file map (section → files, in table
// order) aggregated into one word-frequency map per section.
type corpus struct {
	name        string
	fileMapPath string
	freqMapPath string
	sections    []map[string]int
}

// loadCorpus reads the file map and the per-file freq map, then merges
// each section's file maps into a single map, so freqFinder later does
// one lookup per word per section instead of one per word per file.
func loadCorpus(name string, fileMapPath string, freqMapPath string) *corpus {
	fileMap := []map[string][]string{}
	fileMap = tools.ReadJsonSliceMapStringSliceString(
		filepath.Join(tools.Pth.DpdBaseDir, fileMapPath), fileMap)

	fileFreqMap := map[string]map[string]int{}
	fileFreqMap = tools.ReadJsonMapStringMapStringInt(
		filepath.Join(tools.Pth.DpdBaseDir, freqMapPath), fileFreqMap)

	sections := make([]map[string]int, 0, len(fileMap))
	for _, section := range fileMap {
		sectionMap := map[string]int{}
		for _, fileList := range section {
			for _, fileName := range fileList {
				for word, count := range fileFreqMap[fileName] {
					sectionMap[word] += count
				}
			}
		}
		sections = append(sections, sectionMap)
	}

	return &corpus{
		name:        name,
		fileMapPath: fileMapPath,
		freqMapPath: freqMapPath,
		sections:    sections,
	}
}

func loadCorpora() []*corpus {
	return []*corpus{
		loadCorpus("cst", tools.Pth.CstFileMap, tools.Pth.CstFileFreqMap),
		loadCorpus("bjt", tools.Pth.BjtFileMap, tools.Pth.BjtFileFreqMap),
		loadCorpus("sya", tools.Pth.SyaFileMap, tools.Pth.SyaFileFreqMap),
		loadCorpus("sc", tools.Pth.ScFileMap, tools.Pth.ScFileFreqMap),
	}
}

var htmlStash = map[int]string{}
var dataStash = map[int]string{}
var mu sync.Mutex

func main() {
	tools.PTitle("frequency tables")

	corpora := loadCorpora()
	templ := makeTemplate()

	tools.PGreenTitle("making html & data")
	db, results := getHeadwords()

	numWorkers := runtime.NumCPU() * 2
	jobs := make(chan dpdDb.DpdHeadword, numWorkers*2)

	go func() {
		for index, i := range results {
			if index%10000 == 0 {
				tools.PCounter(index, len(results), i.Lemma1)
			}
			if i.POS != "idiom" {
				jobs <- i
			}
		}
		close(jobs)
	}()

	workerpool.Run(numWorkers, jobs, func(i dpdDb.DpdHeadword) {
		makeFreqTable(i, corpora, templ)
	})

	updateDb(db, results)
	tic.Toc()
}

// getHeadwords loads only the columns makeFreqTable and updateDb need,
// not the full ~60-column rows.
func getHeadwords() (*gorm.DB, []dpdDb.DpdHeadword) {
	db := dpdDb.GetDb()
	var results []dpdDb.DpdHeadword
	err := db.
		Select("id", "lemma_1", "pos", "stem", "inflections",
			"inflections_api_ca_eva_iti").
		Find(&results)
	tools.HardCheck(err.Error)
	return db, results
}

var whiteSpace = regexp.MustCompile(` {2,}`)

// makeTemplate parses the frequency table template, minified once here
// so rendered rows need no per-row whitespace cleaning. The returned
// template is shared by all workers: text/template execution is safe
// for parallel use.
func makeTemplate() *template.Template {
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.FreqTemplateHtml,
	)

	templateRead, err := os.ReadFile(filePath)
	tools.HardCheck(err)

	minified := whiteSpace.ReplaceAllString(string(templateRead), "")
	templ, err := template.New("frequency").Parse(minified)
	tools.HardCheck(err)

	return templ
}

type templateData struct {
	FreqHeading string
	CstFreq     []int
	CstGrad     []int
	BjtFreq     []int
	BjtGrad     []int
	SyaFreq     []int
	SyaGrad     []int
	ScFreq      []int
	ScGrad      []int
}

func makeFreqTable(
	i dpdDb.DpdHeadword,
	corpora []*corpus,
	templ *template.Template,
) {

	wordList := i.InflectionsListALl()

	CstFreqList := freqFinder(wordList, corpora[0])
	BjtFreqList := freqFinder(wordList, corpora[1])
	SyaFreqList := freqFinder(wordList, corpora[2])
	ScFreqList := freqFinder(wordList, corpora[3])

	// colour the gradient of the entire list
	AllFreqList := slices.Concat(
		CstFreqList, BjtFreqList, SyaFreqList, ScFreqList)

	min, max := gradient.MinMax(AllFreqList)

	// template data struct
	td := templateData{}
	html := ""

	if tools.IsAllZero(AllFreqList) {

		heading := fmt.Sprintf("There are no exact matches of <b>%v</b>", i.Lemma1)

		td.FreqHeading = heading
		td.CstFreq = []int{}
		td.CstGrad = []int{}
		td.BjtFreq = []int{}
		td.BjtGrad = []int{}
		td.SyaFreq = []int{}
		td.SyaGrad = []int{}
		td.ScFreq = []int{}
		td.ScGrad = []int{}

	} else {

		var heading string

		if slices.Contains(tools.Indeclinables, i.POS) ||
			strings.HasPrefix(i.Stem, "!") {
			heading = fmt.Sprintf("Frequency of <b>%v</b>", i.Lemma1)

		} else if slices.Contains(tools.Conjugations, i.POS) {
			heading = fmt.Sprintf("Frequency of <b>%v</b> and its conjugations", i.Lemma1)

		} else if slices.Contains(tools.Declensions, i.POS) {
			heading = fmt.Sprintf("Frequency of <b>%v</b> and its declensions", i.Lemma1)
		}

		td.FreqHeading = heading
		td.CstFreq = CstFreqList
		td.CstGrad = gradient.MakeGradients(CstFreqList, min, max)
		td.BjtFreq = BjtFreqList
		td.BjtGrad = gradient.MakeGradients(BjtFreqList, min, max)
		td.SyaFreq = SyaFreqList
		td.SyaGrad = gradient.MakeGradients(SyaFreqList, min, max)
		td.ScFreq = ScFreqList
		td.ScGrad = gradient.MakeGradients(ScFreqList, min, max)

		html = htmlTemplater(td, templ)
	}

	jsonData := tools.JsonMarshall(td)

	mu.Lock()
	htmlStash[i.ID] = html
	dataStash[i.ID] = jsonData
	mu.Unlock()
}

func freqFinder(wordList []string, c *corpus) []int {
	freqList := make([]int, len(c.sections))
	for i, sectionMap := range c.sections {
		for _, word := range wordList {
			freqList[i] += sectionMap[word]
		}
	}
	return freqList
}

func htmlTemplater(td templateData, templ *template.Template) string {
	htmlBuffer := bytes.Buffer{}
	err := templ.Execute(&htmlBuffer, td)
	tools.HardCheck(err)
	return htmlBuffer.String()
}

// updateDb writes the two freq columns with a prepared UPDATE in one
// transaction, instead of deleting and re-inserting the whole table.
func updateDb(db *gorm.DB, results []dpdDb.DpdHeadword) {
	tools.PGreenTitle("updating db")

	sqlDB, err := db.DB()
	tools.HardCheck(err)

	tx, err := sqlDB.Begin()
	tools.HardCheck(err)
	defer tx.Rollback()

	stmt, err := tx.Prepare(
		"UPDATE dpd_headwords SET freq_html = ?, freq_data = ? WHERE id = ?")
	tools.HardCheck(err)

	for _, i := range results {
		_, err = stmt.Exec(htmlStash[i.ID], dataStash[i.ID], i.ID)
		tools.HardCheck(err)
	}

	err = tx.Commit()
	tools.HardCheck(err)
}
