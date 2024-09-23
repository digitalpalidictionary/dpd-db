package splitters

import (
	"dpd/go_modules/deconstructor/data"
	t "dpd/go_modules/tools"
)

/*
Two Word Sandhi Splitter
 1. Split into two words
 2. Apply sandhi rules
 3. Add matches or pass through
*/
func Split2(w data.WordData) {

	if len(w.Middle) <= 3 {
		return
	}

	w.InitNewSplitter()
	data.M.ProcessPlusOne(w)
	word := w.Middle

	// split the words into two parts
	for x := range len(word) - 1 {
		wordA := word[:x+1]
		wordB := word[x+1:]

		// check if wordA & wordB are matches
		if data.G.IsInInflections(wordA) &&
			data.G.IsInInflections(wordB) {

			// add to matches
			w2 := w.MakeCopy()
			w2.ToFront(wordA, wordB)
			w2.ToRuleFront(0)
			w2.AddWeight(2)
			w2.AddPath("2.1")
			data.M.MakeMatch("2.1", w2)
		}

		wordALasLetter := wordA[len(wordA)-1:]
		wordBFirstLetter := wordB[:1]

		// Iterate through all the sandhi rules to find matches
		for _, sr := range data.G.SandhiRules {
			if t.RunesEqual(wordALasLetter, sr.ChA) && t.RunesEqual(wordBFirstLetter, sr.ChB) {

				// replace first and last letters with sandhi rules' letters
				word1 := t.RunesPlus(wordA[:(len(wordA)-1)], sr.Ch1)
				word2 := t.RunesPlus(sr.Ch2, wordB[1:])

				// check if Word1 and Word2 are matches
				if data.G.IsInInflections(word1) &&
					data.G.IsInInflections(word2) {

					// add to matches
					w2 := w.MakeCopy()
					w2.ToFront(word1, word2)
					w2.ToRuleFront(sr.Index)
					w2.AddWeight(sr.Weight)
					w2.AddPath("2.2")
					data.M.MakeMatch("2.2", w2)
				}
			}
		}
	}
}
