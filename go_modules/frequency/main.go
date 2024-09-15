package main

import (
	"bytes"
	"dpd/go_modules/dpdDb"
	"dpd/go_modules/frequency/gradient"
	"dpd/go_modules/tools"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"text/template"

	"gorm.io/gorm"
)

var pf = fmt.Printf
var pl = fmt.Println
var spf = fmt.Sprintf

var t = tools.Tic()

var templ = makeTemplate()

var CstFileMap = []map[string][]string{}
var CstFileFreqMap = map[string]map[string]int{}
var ScFileMap = []map[string][]string{}
var ScFileFreqMap = map[string]map[string]int{}
var BjtFileMap = []map[string][]string{}
var BjtFileFreqMap = map[string]map[string]int{}

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

	// sc fileMap
	filePath = tools.Pth.ScFileMap
	ScFileMap = tools.ReadJsonSliceMapStringSliceString(filePath, ScFileMap)

	// sc fileFreqMap
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.ScFileFreqMap,
	)
	ScFileFreqMap = tools.ReadJsonMapStringMapStringInt(filePath, ScFileFreqMap)

	// bjt fileMap
	filePath = tools.Pth.BjtFileMap
	BjtFileMap = tools.ReadJsonSliceMapStringSliceString(filePath, BjtFileMap)

	// bjt fileFreqMap
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.BjtFileFreqMap,
	)
	BjtFileFreqMap = tools.ReadJsonMapStringMapStringInt(filePath, BjtFileFreqMap)

}

func main() {
	tools.PGreenTitle("making html & data")
	var db, results = dpdDb.GetDpdHeadwords()

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
	t.Toc()
}

func makeTemplate() *template.Template {
	filePath := tools.Pth.CombinedTemplate

	templateRead, err := os.ReadFile(filePath)
	tools.Check(err)

	templ, err := template.New("frequency").Parse(string(templateRead))
	tools.Check(err)

	return templ
}

func cloneTemplate() *template.Template {
	templClone, err := templ.Clone()
	tools.Check(err)
	return templClone
}

type templateData struct {
	Header  string
	CstFreq []int
	CstGrad []int
	BjtFreq []int
	BjtGrad []int
	ScFreq  []int
	ScGrad  []int
}

func makeFreqTable(i dpdDb.DpdHeadword) {

	wordList := i.InflectionsListALl()

	CstFreqList := freqFinder(wordList, CstFileMap, CstFileFreqMap)
	CstGradientList := gradient.MakeGradients(CstFreqList)

	BjtFreqList := freqFinder(wordList, BjtFileMap, BjtFileFreqMap)
	BjtGradientList := gradient.MakeGradients(BjtFreqList)

	ScFreqList := freqFinder(wordList, ScFileMap, ScFileFreqMap)
	ScGradientList := gradient.MakeGradients(ScFreqList)

	// template data struct
	td := templateData{}
	html := ""

	if tools.IsAllZero(CstFreqList) &&
		tools.IsAllZero(BjtFreqList) &&
		tools.IsAllZero(ScFreqList) {

		td.Header = spf("<p>There are no exact matches of <b>%v</b> in any corpus of texts.</p>", i.Lemma1)
		td.CstFreq = []int{}
		td.CstGrad = []int{}
		td.BjtFreq = []int{}
		td.BjtGrad = []int{}
		td.ScFreq = []int{}
		td.ScGrad = []int{}

		html = td.Header

	} else {

		td.Header = makeHeaderString(i.Lemma1, i.POS)
		td.CstFreq = CstFreqList
		td.CstGrad = CstGradientList
		td.BjtFreq = BjtFreqList
		td.BjtGrad = BjtGradientList
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
	tools.Check(err)

	html := htmlBuffer.String()
	html = tools.CleanWhiteSpace(html)

	return html
}

func makeHeaderString(word string, pos string) string {
	posType := tools.TestPosType(pos)
	var headerString string

	switch posType {
	case "indeclinable":
		headerString = spf("Frequency of <b>%v</b>", word)
	case "conjugation":
		headerString = spf("Frequency of <b>%v</b> and its conjugations", word)
	case "declension":
		headerString = spf("Frequency of <b>%v</b> and its declensions", word)
	default:
		tools.PRed("some error occurred making the header string")
	}

	return headerString
}

func saveHtmlFile(html string) {
	tools.PGreenTitle("saving html test")

	// dpdCss
	dpdCss, err := os.ReadFile(filepath.Join(tools.Pth.DpdBaseDir, tools.Pth.DpdCss))
	tools.Check(err)

	finalHtml := spf("<style>\n%v\n</style>\n<body>\n%v</body>\n", string(dpdCss), string(html))

	saveFile, err := os.Create("htmlTest.html")
	tools.Check(err)
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
