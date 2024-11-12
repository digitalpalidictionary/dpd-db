package main

import (
	"dpd/go_modules/deconstructor/data"
	"dpd/go_modules/deconstructor/importer"
	"dpd/go_modules/deconstructor/splitters"
	"dpd/go_modules/tools"
	"maps"
	"sync"
)

var tic = tools.Tic()
var Wg = sync.WaitGroup{}

var doNotRun = !((tools.IniTest("exporter", "make_deconstructor", "yes") ||
	tools.IniTest("exporter", "make_tpr", "yes") ||
	tools.IniTest("exporter", "make_ebook", "yes") ||
	tools.IniTest("regenerate", "db_rebuild", "yes")) &&
	tools.IniTest("deconstructor", "use_premade", "no"))

func init() {
	tools.PTitle("deconstructing compounds")

	if doNotRun {
		tools.PGreenTitle("disabled in config.ini")
		return
	}

	// init globals
	var di = importer.DeconImporter()
	data.M.MatchedItems = di.MatchItemList
	data.M.Unmatched = di.Unmatched1

	data.G.Unmatched = di.Unmatched2
	data.G.AllInflections = di.AllInflections
	data.G.AllInflectionsNoFirst = di.AllInflectionsNoFirst
	data.G.AllInflectionsNoLast = di.AllInflectionsNoLast
	data.G.SandhiRules = di.SandhiRules
}

func main() {

	if doNotRun {
		tic.Toc()
		return
	}

	// only for testing
	tools.PGreenTitle("splitting compounds")
	testSet := map[string]string{
		// "lūnāvasiṭṭhavisukkhatiladaṇḍakā": "",
	}
	if len(testSet) > 0 {
		data.G.Unmatched = maps.Clone(testSet)
		data.M.Unmatched = maps.Clone(testSet)
	}

	counter := 1
	for word := range data.G.Unmatched {
		if counter%data.L.CountEvery == 0 {
			tools.PCounter(counter, len(data.G.Unmatched), word)
		}

		w := data.InitWordData(tools.Str2Rune(word))

		if len(w.Middle) <= 3 {
			continue
		}

		if len(w.Word) < data.L.MaxWordLength || data.L.MaxWordLength == 0 {
			Wg.Add(1)
			if data.L.Recursive {
				go deconstruct(w)
			} else {
				deconstruct(w)
			}
		}
		counter++
	}

	Wg.Wait()
	data.M.Summary()
	data.M.SaveMatchedTsv()
	data.M.SaveUnmatchedTsv()
	data.M.SaveTopEntriesJson()
	data.M.SaveStatsTsv()

	if data.L.WordLimit == 0 && len(testSet) == 0 {
		data.M.SaveToDb()
	}

	tic.Toc()
}

func deconstruct(w data.WordData) {
	splitters.Split2(w)
	splitters.Split3(w)
	splitters.SplitRecursive(w)
	Wg.Done()
	data.M.SaveWordStats(w)
}
