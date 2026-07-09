package main

import (
	"dpd/go_modules/deconstructor/data"
	"dpd/go_modules/deconstructor/importer"
	"dpd/go_modules/deconstructor/splitters"
	"dpd/go_modules/deconstructor/workerpool"
	"dpd/go_modules/tools"
	"maps"
	"os"
	"path/filepath"
	"runtime"
)

var tic = tools.Tic()
var doNotRun = !tools.IniTest("generate", "deconstructor", "yes")

func init() {
	tools.PTitle("deconstructing compounds")

	if doNotRun {
		tools.PGreenTitle("disabled in config.ini")
		return
	}

	// init globals
	var di = importer.DeconImporter()
	data.M.ManualCorrections = di.MatchItemList
	data.M.Unmatched = di.Unmatched1

	data.G.Unmatched = di.Unmatched2
	data.G.AllInflections = di.AllInflections
	data.G.AllInflectionsNoFirst = di.AllInflectionsNoFirst
	data.G.AllInflectionsNoLast = di.AllInflectionsNoLast
	data.G.SandhiRuleIndex = di.SandhiRuleIndex
}

func main() {

	if doNotRun {
		tic.Toc()
		return
	}

	// only for testing
	tools.PGreenTitle("loading go routines")
	testSet := map[string]string{
		// "ūrujaghanathanadassanādikaṃ": "",
	}
	if len(testSet) > 0 {
		data.G.Unmatched = maps.Clone(testSet)
		data.M.Unmatched = maps.Clone(testSet)
	}

	// Per-worker match rows are streamed to files in this temp dir, then
	// concatenated into matches.tsv and removed.
	outputDir := filepath.Dir(tools.Pth.DeconstructorOutput)
	tempDir, err := os.MkdirTemp(outputDir, "worker_tmp_")
	tools.HardCheck(err)
	// Always remove the temp dir — including on a mid-run panic (e.g. disk-full),
	// so a failed local run never orphans multi-GB worker files.
	defer os.RemoveAll(tempDir)

	// Bounded worker pool: NumCPU*2 workers pull from a buffered channel.
	// Replaces the previous unbounded goroutine-per-word pattern that caused
	// scheduler thrashing at ~1M goroutines.
	numWorkers := runtime.NumCPU() * 2
	jobs := make(chan data.WordData, numWorkers*2)

	total := len(data.G.Unmatched)
	go func() {
		counter := 1
		for word := range data.G.Unmatched {
			if counter%data.L.CountEvery == 0 {
				tools.PCounter(counter, total, word)
			}
			w := data.InitWordData(tools.Str2Rune(word))
			if len(w.Middle) <= 3 {
				counter++
				continue
			}
			if len(w.Word) < data.L.MaxWordLength || data.L.MaxWordLength == 0 {
				jobs <- w
			}
			counter++
		}
		close(jobs)
	}()

	accs := workerpool.RunCollect(numWorkers, data.NewWorkerFactory(tempDir), jobs, deconstruct)
	data.CloseWorkers(accs)
	data.M.Merge(accs)
	data.M.Summary()
	data.M.SaveMatchedTsv(accs)
	data.M.SaveUnmatchedTsv()
	data.M.SaveTopEntriesJson()
	data.M.SaveStatsTsv()

	// The lookup.deconstructor column is written by the Python step
	// scripts/build/deconstructor_output_add_to_db.py, which reads the
	// deconstructor_output.json produced above and syncs it via the targeted
	// upsert in tools/lookup_sync.py (not a DELETE-and-rebuild).

	tic.Toc()
}

func deconstruct(acc *data.MatchData, w data.WordData) {
	acc.ResetWord()
	w.Acc = acc
	splitters.Split2(w)
	splitters.Split3(w)
	splitters.SplitRecursive(w)
	acc.SaveWordStats(w)
	acc.FinishWord()
}
