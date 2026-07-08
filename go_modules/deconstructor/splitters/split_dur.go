package splitters

import (
	"dpd/go_modules/deconstructor/data"
)

func SplitDur(w data.WordData) {

	if len(w.Middle) > 3 {

		w.InitNewSplitter()
		w.Acc.ProcessPlusOne(w)
		word := w.Middle
		w.RecurseFlag = true
		processName := "dur"

		w.Front = append(w.Front, "dur")
		w.ToRuleFront(0)
		w.AddWeight(2)

		if word[2] == word[3] {
			// dur followed by double consonant "dubbhāsita"
			w.Middle = word[3:]
			processName = "dur1"
			w.AddPath(processName)
		} else {
			// dur followed by single vowel "dur-accaya"
			w.Middle = word[3:]
			processName = "dur2"
			w.AddPath(processName)
		}

		// TODO How to handle "du-rakkhiya"?

		if data.G.IsInInflections(w.Middle) {
			w.Acc.MakeMatch(processName, w)
		} else {
			SplitRecursive(w)
		}
	}
}
