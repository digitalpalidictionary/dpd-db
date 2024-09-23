package splitters

import (
	"dpd/go_modules/deconstructor/data"
)

func SplitSa(w data.WordData) {

	if len(w.Middle) > 2 {

		w.InitNewSplitter()
		data.M.ProcessPlusOne(w)
		word := w.Middle
		w.Front = append(w.Front, "sa")
		w.RecurseFlag = true
		processName := "sa"

		if word[2] == word[3] {
			// sa followed by double consonant "saddara"
			w.Middle = word[3:]
			processName = "sa1"
			w.AddPath("sa1")
		} else {
			// sa followed by single consonant "sadevaka"
			w.Middle = word[2:]
			processName = "sa2"
			w.AddPath("sa2")
		}

		if data.G.IsInInflections(w.Middle) {
			w.ToRuleFront(0)
			w.AddWeight(2)
			data.M.MakeMatch(processName, w)
		} else {
			w.ToRuleFront(0)
			w.AddWeight(2)
			SplitRecursive(w)
		}
	}
}
