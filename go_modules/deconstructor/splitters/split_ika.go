package splitters

import (
	"dpd/go_modules/deconstructor/data"
	t "dpd/go_modules/tools"
	"strings"
)

func SplitIka(w data.WordData) {
	w.InitNewSplitter()
	w.Acc.ProcessPlusOne(w)
	word := w.Middle
	w.RecurseFlag = true
	processName := "ika"

	suffixes := []string{
		"iko", "ikā", "ikāse", "ikāyo", "ikaṃ", "ikāni", "ike",
		"ikena", "ikebhi", "ikehi", "ikāya", "ikābhi", "ikāhi",
		"ikassa", "ikānaṃ", "ikato", "ikamhā", "ikasmā",
		"ikamhi", "ikasmiṃ", "ikesu", "ikāsu",
	}

	for _, suffix := range suffixes {
		if strings.HasSuffix(string(word), suffix) && len(w.Middle) > len(suffix)+2 {

			suffixLen := len(t.Str2Rune(suffix))
			// build the stem in fresh memory then add the 'a' back — appending
			// into word[:...] would overwrite the shared backing array in place
			// and corrupt the original word (e.g. gāmikā -> gāmakā).
			stem := word[:len(word)-suffixLen]
			middle := make([]rune, len(stem)+1)
			copy(middle, stem)
			middle[len(stem)] = 'a'
			back := t.Str2Rune(suffix)
			w.ToBack(middle, back)
			processName = suffix
			w.AddPath(processName)

			if data.G.IsInInflections(w.Middle) {
				w.ToRuleBack(0)
				w.AddWeight(2)
				w.Acc.MakeMatch(processName, w)
			} else {
				w.ToRuleBack(0)
				w.AddWeight(2)
				SplitRecursive(w)
			}
			break
		}
	}
}
