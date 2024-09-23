package splitters

import (
	"dpd/go_modules/deconstructor/data"
	t "dpd/go_modules/tools"
	"strings"
)

func SplitTta(w data.WordData) {

	if len(w.Middle) > 3 {

		w.InitNewSplitter()
		data.M.ProcessPlusOne(w)
		word := w.Middle
		w.RecurseFlag = true
		processName := "tta"

		if strings.HasSuffix(string(word), "tta") {
			middle := word[:len(word)-3]
			back := t.Str2Rune("tta")
			w.ToBack(middle, back)
			processName = "tta"
			w.AddPath(processName)

		} else if strings.HasSuffix(string(word), "ttā") {
			middle := word[:len(word)-3]
			back := t.Str2Rune("ttā")
			w.ToBack(middle, back)
			processName = "ttā"
			w.AddPath(processName)

		} else if strings.HasSuffix(string(word), "tā") {
			middle := word[:len(word)-2]
			back := t.Str2Rune("tā")
			w.ToBack(middle, back)
			processName = "tā"
			w.AddPath(processName)

		} else if strings.HasSuffix(string(word), "tāya") {
			middle := word[:len(word)-4]
			back := t.Str2Rune("tāya")
			w.ToBack(middle, back)
			processName = "tāya"
			w.AddPath(processName)

		} else if strings.HasSuffix(string(word), "tāyaṃ") {
			middle := word[:len(word)-5]
			back := t.Str2Rune("tāyaṃ")
			w.ToBack(middle, back)
			processName = "tāyaṃ"
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
