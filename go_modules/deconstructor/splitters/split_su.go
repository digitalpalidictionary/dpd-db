package splitters

import (
	"gm/deconstructor/data"
)

func SplitSu(w data.WordData) {

	if len(w.Middle) > 3 {

		w.InitNewSplitter("su")
		data.M.ProcessPlusOne(w)
		word := w.Middle
		w.Front = append(w.Front, "su")
		w.RecurseFlag = true
		processName := "su"

		if word[2] == word[3] {
			// su followed by double consonant "succhanna"
			w.Middle = word[3:]
			processName = "su-dd"
		} else {
			// su followed by single consonant "sucitti"
			w.Middle = word[2:]
			processName = "su"
		}

		if data.G.IsInInflections(w.Middle) {
			w.ToRuleFront("0")
			w.AddWeight(2)
			data.M.MakeMatch(processName, w)
		} else {
			w.ToRuleFront("0")
			w.AddWeight(2)
			SplitRecursive(w)
		}
	}
}
