package main

import (
	"dpd/go_modules/dpdDb"
	"dpd/go_modules/tools"
	"path/filepath"
	"slices"
)

// Calculate the number of occurrences of a word's inflections in early texts and add to db.
// EBT books are vin1-4, four nikāyas and kn1

// abandoned cos updating the db is too slow in go.
// TODO chop up and delete

func main() {

	t := tools.Tic()
	tools.PTitle("Calculating word frequency in EBTs")

	tools.PGreenTitle("setting up")
	ebtFiles := makeEbtFileList()
	CstFileFreqMap := importCstFileFreqMap()

	db, dpdHeadwords := dpdDb.GetDpdHeadword()
	ebtDict := map[int]int{}

	tools.PGreenTitle("calculating")
	for _, i := range dpdHeadwords {
		counter := 0
		inflections := i.InflectionsListALl()
		for _, inflection := range inflections {
			for _, ebtFile := range ebtFiles {
				counter = counter + CstFileFreqMap[ebtFile][inflection]
			}
		}
		ebtDict[i.ID] = counter
	}

	tools.PGreenTitle("adding to db")
	for id, value := range ebtDict {
		dpdDb.UpdateHeadwordSingleColumnInt(db, id, "ebt_count", value)
	}

	t.Toc()

}

// make a list of EBT files
func makeEbtFileList() []string {

	filePath := filepath.Join(tools.Pth.DpdBaseDir, tools.Pth.CstFileMap)
	var CstFileMap = []map[string][]string{}
	CstFileMap = tools.ReadJsonSliceMapStringSliceString(filePath, CstFileMap)

	var ebtBooks = []string{
		"vin1", "vin2", "vin3", "vin4",
		"dn", "mn", "sn", "an", "kn1",
	}

	var ebtFiles = []string{}

	for _, data := range CstFileMap {
		for book, fileList := range data {
			if slices.Contains(ebtBooks, book) {
				ebtFiles = append(ebtFiles, fileList...)
			}
		}
	}
	return ebtFiles
}

// import the CST file frequency map
func importCstFileFreqMap() map[string]map[string]int {
	var CstFileFreqMap = map[string]map[string]int{}
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.CstFileFreqMap,
	)
	return tools.ReadJsonMapStringMapStringInt(filePath, CstFileFreqMap)

}
