package main

import (
	"dpd/go_modules/deconstructor/data"
	"dpd/go_modules/deconstructor/importer"
	"fmt"

	"dpd/go_modules/deconstructor/splitters"
	"dpd/go_modules/tools"
	"sync"
)

// printers
var pl = fmt.Println
var pf = fmt.Printf
var spf = fmt.Sprintf

var Wg = sync.WaitGroup{}

func init() {
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
	pl("Deconstructing compounds")

	testMap := map[string]string{
		// "ādīnavānisaṃsadassanavidhi": "",
	}
	if len(testMap) > 0 {
		data.G.Unmatched = testMap
		data.M.Unmatched = testMap
	}

	counter := 1
	for word := range data.G.Unmatched {
		if counter%data.L.Counter == 0 {
			pl(counter, "/", len(data.G.Unmatched), word)
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
		data.M.SaveWordStats(w)
		counter++
	}

	Wg.Wait()
	data.M.Summary()
	data.M.SaveMatchedTsv()
	data.M.SaveUnmatchedTsv()
	data.M.SaveTopEntriesJson()
	data.M.SaveToDb()
	data.M.SaveStatsTsv()
}

func deconstruct(w data.WordData) {
	splitters.Split2(w)
	splitters.Split3(w)
	splitters.SplitRecursive(w)
	Wg.Done()
}
