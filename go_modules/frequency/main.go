package main

import (
	"bytes"
	"dpd/go_modules/dpdDb"
	"dpd/go_modules/frequency/gradient"
	"dpd/go_modules/tools"
	"fmt"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"sync"
	"text/template"

	"gorm.io/gorm"
)

var tic = tools.Tic()

var templ = makeTemplate()

var CstFileMap = []map[string][]string{}
var CstFileFreqMap = map[string]map[string]int{}
var BjtFileMap = []map[string][]string{}
var BjtFileFreqMap = map[string]map[string]int{}
var SyaFileMap = []map[string][]string{}
var SyaFileFreqMap = map[string]map[string]int{}
var ScFileMap = []map[string][]string{}
var ScFileFreqMap = map[string]map[string]int{}

var htmlStash = map[int]string{}
var dataStash = map[int]string{}
var wg sync.WaitGroup
var mu sync.Mutex

func init() {
	tools.PTitle("frequency tables")

	// cst fileMap
	filePath := tools.Pth.CstFileMap
	CstFileMap = tools.ReadJsonSliceMapStringSliceString(filePath, CstFileMap)

	// cst fileFreqMap
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.CstFileFreqMap,
	)
	CstFileFreqMap = tools.ReadJsonMapStringMapStringInt(filePath, CstFileFreqMap)

	// bjt fileMap
	filePath = tools.Pth.BjtFileMap
	BjtFileMap = tools.ReadJsonSliceMapStringSliceString(filePath, BjtFileMap)

	// bjt fileFreqMap
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.BjtFileFreqMap,
	)
	BjtFileFreqMap = tools.ReadJsonMapStringMapStringInt(filePath, BjtFileFreqMap)

	// sya fileMap
	filePath = tools.Pth.SyaFileMap
	SyaFileMap = tools.ReadJsonSliceMapStringSliceString(filePath, SyaFileMap)

	// sya fileFreqMap
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.SyaFileFreqMap,
	)
	SyaFileFreqMap = tools.ReadJsonMapStringMapStringInt(filePath, SyaFileFreqMap)

	// sc fileMap
	filePath = tools.Pth.ScFileMap
	ScFileMap = tools.ReadJsonSliceMapStringSliceString(filePath, ScFileMap)

	// sc fileFreqMap
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.ScFileFreqMap,
	)
	ScFileFreqMap = tools.ReadJsonMapStringMapStringInt(filePath, ScFileFreqMap)

}

func main() {
	tools.PGreenTitle("making html & data")
	var db, results = dpdDb.GetDpdHeadword()

	for index, i := range results {
		if index%10000 == 0 {
			tools.PCounter(index, len(results), i.Lemma1)
		}
		if i.POS != "idiom" {
			wg.Add(1)
			go makeFreqTable(i)
		}
	}
	wg.Wait()
	updateDb(db, results)
	tic.Toc()
}

func makeTemplate() *template.Template {
	filePath := tools.Pth.FreqTemplateHtml

	templateRead, err := os.ReadFile(filePath)
	tools.HardCheck(err)

	templ, err := template.New("frequency").Parse(string(templateRead))
	tools.HardCheck(err)

	return templ
}

func cloneTemplate() *template.Template {
	templClone, err := templ.Clone()
	tools.HardCheck(err)
	return templClone
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

func makeFreqTable(i dpdDb.DpdHeadword) {

	wordList := i.InflectionsListALl()

	CstFreqList := freqFinder(wordList, CstFileMap, CstFileFreqMap)
	BjtFreqList := freqFinder(wordList, BjtFileMap, BjtFileFreqMap)
	SyaFreqList := freqFinder(wordList, SyaFileMap, SyaFileFreqMap)
	ScFreqList := freqFinder(wordList, ScFileMap, ScFileFreqMap)

	// colour the gradient of the entire list
	AllFreqList := slices.Concat(
		CstFreqList, BjtFreqList, SyaFreqList, ScFreqList)

	min, max := gradient.MinMax(AllFreqList)

	CstGradientList := gradient.MakeGradients(CstFreqList, min, max)
	BjtGradientList := gradient.MakeGradients(BjtFreqList, min, max)
	SyaGradientList := gradient.MakeGradients(SyaFreqList, min, max)
	ScGradientList := gradient.MakeGradients(ScFreqList, min, max)

	// template data struct
	td := templateData{}
	html := ""

	if tools.IsAllZero(CstFreqList) &&
		tools.IsAllZero(BjtFreqList) &&
		tools.IsAllZero(ScFreqList) {

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

		html = ""

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
		td.CstGrad = CstGradientList
		td.BjtFreq = BjtFreqList
		td.BjtGrad = BjtGradientList
		td.SyaFreq = SyaFreqList
		td.SyaGrad = SyaGradientList
		td.ScFreq = ScFreqList
		td.ScGrad = ScGradientList

		html = htmlTemplater(td)
	}

	jsonData := tools.JsonMarshall(td)

	mu.Lock()
	htmlStash[i.ID] = html
	dataStash[i.ID] = jsonData
	mu.Unlock()

	wg.Done()
}

func freqFinder(
	wordList []string,
	fileMap []map[string][]string,
	fileFreqMap map[string]map[string]int,
) []int {

	freqList := []int{}
	for _, section := range fileMap {
		sectionCount := 0
		for _, fileList := range section {
			for _, fileName := range fileList {
				for _, word := range wordList {
					wordCount := fileFreqMap[fileName][word]
					sectionCount = sectionCount + wordCount
				}
			}
		}
		freqList = append(freqList, sectionCount)
	}
	return freqList
}

func htmlTemplater(td templateData) string {
	t := cloneTemplate()

	htmlBuffer := bytes.Buffer{}
	err := t.Execute(&htmlBuffer, td)
	tools.HardCheck(err)

	html := htmlBuffer.String()
	html = tools.CleanWhiteSpace(html)

	return html
}

func saveHtmlFile(html string) {
	tools.PGreenTitle("saving html test")

	// dpdCss
	dpdCss, err := os.ReadFile(filepath.Join(tools.Pth.DpdBaseDir, tools.Pth.DpdCss))
	tools.HardCheck(err)

	finalHtml := fmt.Sprintf("<style>\n%v\n</style>\n<body>\n%v</body>\n", string(dpdCss), string(html))

	saveFile, err := os.Create("htmlTest.html")
	tools.HardCheck(err)
	saveFile.Write([]byte(finalHtml))
}

func updateDb(db *gorm.DB, results []dpdDb.DpdHeadword) {
	tools.PGreenTitle("updating db")

	updatedResults := []dpdDb.DpdHeadword{}

	for _, i := range results {
		i.FreqHtml = htmlStash[i.ID]
		i.FreqData = dataStash[i.ID]
		updatedResults = append(updatedResults, i)
	}

	tx := db.Begin()
	defer dpdDb.Rollback(tx)

	// wipe the table clean
	tx.Exec("DELETE FROM dpd_headwords")

	// add the updated rows
	tx.CreateInBatches(&updatedResults, 500)
	tx.Commit()
}
