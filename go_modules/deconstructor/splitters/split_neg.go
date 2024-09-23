package splitters

import (
	"dpd/go_modules/deconstructor/data"
	t "dpd/go_modules/tools"
)

func SplitNeg(w data.WordData) {

	if len(w.Middle) > 3 {

		w.InitNewSplitter()
		data.M.ProcessPlusOne(w)
		word := w.Middle
		w.Front = append(w.Front, "na")
		w.RecurseFlag = true
		processName := "neg"

		if w.StartsWith("na") {

			if word[2] == word[3] {
				// na-ppahoti
				w.Middle = word[3:]
				processName = "neg1"
				w.AddPath(processName)
			} else {
				// na-khudda
				w.Middle = word[2:]
				processName = "neg2"
				w.AddPath(processName)
			}

		} else if w.StartsWith("an") {
			w.Middle = word[2:]
			processName = "neg3"
			w.AddPath(processName)

		} else if w.StartsWith("nā") {
			w.Middle = t.Str2Rune("a" + string(w.Middle[2:]))
			processName = "neg4"
			w.AddPath(processName)

		} else if w.StartsWith("a") {

			if word[1] == word[2] {
				// a-ññāṇa
				w.Middle = word[2:]
				processName = "neg5"
				w.AddPath(processName)

			} else {
				//  a-samaṇā
				w.Middle = word[1:]
				processName = "neg6"
				w.AddPath(processName)
			}
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
