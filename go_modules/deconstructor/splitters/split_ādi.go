package splitters

import (
	"dpd/go_modules/deconstructor/data"
	t "dpd/go_modules/tools"
)

func SplitAdi(w data.WordData) {

	if len(w.Middle) > 3 {

		w.InitNewSplitter()
		data.M.ProcessPlusOne(w)
		word := w.Middle
		w.RecurseFlag = true
		processName := "ādi"

		var wordA, wordB []rune
		wordA = word[:len(word)-3]
		wordB = word[len(word)-3:]

		wordALastRune := wordA[len(wordA)-1]
		wordBFirstRune := wordB[0]

		// O(k) index lookup: returns only rules matching this rune pair (~1-5),
		// replacing a full scan of all ~300 sandhi rules per split position.
		// IsConsonant guard moved here (equivalent: index key IS wordALastRune).
		if t.IsConsonant(wordALastRune) {
			for _, sr := range data.G.SandhiRuleIndex[wordALastRune][wordBFirstRune] {

				// replace first and last letters with sandhi rules' letters
				word1 := t.RunesPlus(wordA[:(len(wordA)-1)], sr.Ch1)
				word2 := t.RunesPlus(sr.Ch2, wordB[1:])

				// check if word1 and word2 are matches
				if data.G.IsInInflections(word1) &&
					data.G.IsInInflections(word2) {

					w2 := w.MakeCopy()
					w2.ToBack(word1, word2)
					w2.ToRuleBack(sr.Index)
					w2.AddWeight(sr.Weight)
					w2.AddPath("ādi")
					data.M.MakeMatch(processName, w2)

				} else if string(word2) == "ādi" {
					// check if word2 is ādi and recurse
					w2 := w.MakeCopy()
					w2.ToBack(word1, word2)
					w2.ToRuleBack(sr.Index)
					w2.AddWeight(sr.Weight)
					w2.AddPath("ādi")
					SplitRecursive(w2)
				}
			}
		}
	}
}
