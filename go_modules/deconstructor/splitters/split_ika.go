package splitters

import (
	"dpd/go_modules/deconstructor/data"
	t "dpd/go_modules/tools"
	"strings"
)

func SplitIka(w data.WordData) {
	word := w.Middle
	w.RecurseFlag = true
	processName := "ka"

	suffixes := []string{
		"iko", "ikā", "ikāse", "ikāyo", "ikaṃ", "ikāni", "ike",
		"ikena", "ikebhi", "ikehi", "ikāya", "ikābhi", "ikāhi",
		"ikassa", "ikānaṃ", "ikato", "ikamhā", "ikasmā",
		"ikamhi", "ikasmiṃ", "ikesu", "ikāsu"}
	for _, suffix := range suffixes {
		if strings.HasSuffix(string(word), suffix) && len(w.Middle) > len(suffix)+2 {
			w.InitNewSplitter()
			data.M.ProcessPlusOne(w)
			suffixLen := len(suffix)
			middle := append(word[:len(word)-suffixLen], 'a') // add the letter 'a' back
			back := t.Str2Rune(suffix)
			w.ToBack(middle, back)
			processName = suffix
			w.AddPath(processName)

			if data.G.IsInInflections(w.Middle) {
				w.ToRuleBack(0)
				w.AddWeight(2)
				data.M.MakeMatch(processName, w)
			} else {
				w.ToRuleBack(0)
				w.AddWeight(2)
				SplitRecursive(w)
			}
			break
		}
	}
}
