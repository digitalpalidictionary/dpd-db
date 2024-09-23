package splitters

import (
	"dpd/go_modules/deconstructor/data"
	t "dpd/go_modules/tools"
	"strings"
)

func SplitTissa(w data.WordData) {

	if len(w.Middle) > 5 {

		w.InitNewSplitter()
		data.M.ProcessPlusOne(w)
		word := w.Middle
		w.RecurseFlag = true
		processName := "tissa"

		if strings.HasSuffix(string(word), "tissa") {
			middle := word[:len(word)-5]
			back := t.Str2Rune("iti + assa")
			w.ToBack(middle, back)
			processName = "tissa"
			w.AddPath(processName)

		} else if strings.HasSuffix(string(word), "tissā") {
			middle := word[:len(word)-5]
			back := t.Str2Rune("iti + assā")
			w.ToBack(middle, back)
			processName = "tissā"
			w.AddPath(processName)
		}

		if data.G.IsInInflections(w.Middle) {
			w.ToRuleBack(0)
			w.AddWeight(2)
			data.M.MakeMatch(processName, w)
		} else {
			w.ToRuleBack(0)
			w.AddWeight(2)
			SplitRecursive(w)
		}
	}
}
