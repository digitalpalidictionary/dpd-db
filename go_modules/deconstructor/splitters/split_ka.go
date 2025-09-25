package splitters

import (
	"dpd/go_modules/deconstructor/data"
	t "dpd/go_modules/tools"
	"strings"
)

func SplitKa(w data.WordData) {

	if len(w.Middle) > 6 {

		w.InitNewSplitter()
		data.M.ProcessPlusOne(w)
		word := w.Middle
		w.RecurseFlag = true
		processName := "ka"

		suffixes := []string{
			"ko", "kā", "kāse", "kāyo", "kaṃ", "kāni", "ke", 
			"kena", "kebhi", "kehi", "kāya", "kābhi", "kāhi", 
			"kassa", "kānaṃ", "kato", "kamhā", "kasmā", 
			"kamhi", "kasmiṃ", "kesu", "kāsu"}
		for _, suffix := range suffixes {
			if strings.HasSuffix(string(word), suffix) {
				suffixLen := len(suffix)
				middle := word[:len(word)-suffixLen]
				back := t.Str2Rune(suffix)
				w.ToBack(middle, back)
				processName = suffix
				w.AddPath(processName)
				break
			}
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
