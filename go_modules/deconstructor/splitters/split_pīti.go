package splitters

import (
	"dpd/go_modules/deconstructor/data"
	t "dpd/go_modules/tools"
)

func SplitPiti(w data.WordData) {

	if len(w.Middle) > 5 {

		w.InitNewSplitter()
		data.M.ProcessPlusOne(w)
		word := w.Middle
		w.RecurseFlag = true
		processName := "pīti"

		var wordA, wordB []rune
		wordA = word[:len(word)-5]
		wordB = word[len(word)-5:]

		wordALastRune := wordA[len(wordA)-1]
		wordBFirstRune := wordB[0]

		// O(k) index lookup: returns only rules matching this rune pair (~1-5),
		// replacing a full scan of all ~300 sandhi rules per split position.
		for _, sr := range data.G.SandhiRuleIndex[wordALastRune][wordBFirstRune] {

			// replace first and last letters with sandhi rules' letters
			word1 := t.RunesPlus(wordA[:(len(wordA)-1)], sr.Ch1)
			word2 := t.RunesPlus(sr.Ch2, wordB[1:])

			if data.G.IsInInflections(word1) &&
				string(word2) == "apīti" {

				// update and match
				w2 := w.MakeCopy()
				w2.ToBack(word1, t.Str2Rune("api + iti"))
				w2.ToRuleBack(sr.Index)
				w2.AddWeight(sr.Weight)
				w2.AddPath("pīti")
				data.M.MakeMatch(processName, w2)

			} else if string(word2) == "apīti" {

				// check if word2 is apīti and recurse
				w2 := w.MakeCopy()
				w2.ToBack(word1, t.Str2Rune("api + iti"))
				w2.ToRuleBack(sr.Index)
				w2.AddWeight(sr.Weight)
				w2.AddPath("pīti")
				SplitRecursive(w2)
			}
		}
	}
}
