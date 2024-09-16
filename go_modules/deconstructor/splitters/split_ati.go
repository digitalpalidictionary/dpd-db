package splitters

import (
	"dpd/go_modules/deconstructor/data"
)

func SplitAti(w data.WordData) {

	if len(w.Middle) > 5 {

		w.InitNewSplitter("ati")
		data.M.ProcessPlusOne(w)
		word := w.Middle
		w.RecurseFlag = true
		processName := "ati"

		w.Front = append(w.Front, "ati")
		w.ToRuleFront("0")
		w.AddWeight(2)

		if word[3] == word[4] {
			// ati followed by double consonant "atikkamati"
			w.Middle = word[4:]
			processName = "ati-dd"
		} else {
			// ati followed by single consonant "atikisa"
			w.Middle = word[3:]
			processName = "ati"
		}

		if data.G.IsInInflections(w.Middle) {
			data.M.MakeMatch(processName, w)

		} else {
			SplitRecursive(w)
		}
	}
}
