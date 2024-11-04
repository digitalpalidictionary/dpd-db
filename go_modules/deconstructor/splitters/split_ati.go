package splitters

import (
	"dpd/go_modules/deconstructor/data"
)

func SplitAti(w data.WordData) {

	if len(w.Middle) > 5 {

		w.InitNewSplitter()
		data.M.ProcessPlusOne(w)
		word := w.Middle
		w.RecurseFlag = true
		processName := "ati"

		if w.StartsWith("ati") {

			if word[3] == word[4] {
				// ati followed by double consonant "atikkamati"
				w.Front = append(w.Front, "ati")
				w.ToRuleFront(0)
				w.AddWeight(2)
				w.Middle = word[4:]
				processName = "ati1"
				w.AddPath(processName)
			} else {
				// ati followed by single consonant "atikisa"
				w.Front = append(w.Front, "ati")
				w.ToRuleFront(0)
				w.AddWeight(2)
				w.Middle = word[3:]
				processName = "ati2"
				w.AddPath(processName)
			}

		} else if w.StartsWith("nāti") {

			if word[4] == word[5] {
				// na ati followed by double consonant "nātikkamati"
				w.Front = append(w.Front, "na + ati")
				w.ToRuleFront(0)
				w.AddWeight(2)
				w.Middle = word[5:]
				processName = "nāti1"
				w.AddPath(processName)
			} else {
				// na ati followed by single consonant "nātikisa"
				w.Front = append(w.Front, "na + ati")
				w.ToRuleFront(0)
				w.AddWeight(2)
				w.Middle = word[4:]
				processName = "nāti2"
				w.AddPath(processName)
			}

		}

		if data.G.IsInInflections(w.Middle) {
			data.M.MakeMatch(processName, w)

		} else {
			SplitRecursive(w)
		}
	}
}
