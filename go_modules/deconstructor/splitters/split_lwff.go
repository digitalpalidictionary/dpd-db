package splitters

import (
	"dpd/go_modules/deconstructor/data"
	t "dpd/go_modules/tools"
)

func SplitLwff(w data.WordData) {

	if len(w.Middle) <= 3 {
		return
	}

	w.InitNewSplitter()
	data.M.ProcessPlusOne(w)
	word := w.Middle
	w.RecurseFlag = true
	w.LwffLwfbFlag = true

	// Compile a list of all the longest recognized words,
	// 'clean' means without sandhi
	// 'fuzzy' means with sandhi

	lwffCleanList := [][]rune{}
	lwffFuzzyList := [][]rune{}

	for i := range len(word) {
		lwff := word[:len(word)-i]

		if data.G.IsInInflections(lwff) {
			lwffCleanList = append(lwffCleanList, lwff)
		}

		if data.G.IsInInflectionNoLast(lwff) {
			lwffFuzzyList = append(lwffFuzzyList, lwff)
		}
	}

	// Limit the size of the lists if not the first process
	if w.ProcessCount != 0 {
		if len(lwffCleanList) >= data.L.LwCleanListMaxLen &&
			data.L.LwCleanListMaxLen != 0 {
			lwffCleanList = lwffCleanList[:data.L.LwCleanListMaxLen]
		}
		if len(lwffFuzzyList) >= data.L.LwFuzzyListMaxLen &&
			data.L.LwFuzzyListMaxLen != 0 {
			lwffFuzzyList = lwffFuzzyList[:data.L.LwFuzzyListMaxLen]
		}
	}

	// Process lwffCleanList
	for _, lwffClean := range lwffCleanList {
		w2 := w.MakeCopy()
		middle := w.RemainderAfter(lwffClean)

		if len(middle) >= data.L.LwCleanMinLen {
			if data.G.IsInInflections(middle) {
				w2.ToFront(lwffClean, middle)
				w2.ToRuleFront(0)
				w2.AddWeight(2)
				w2.AddPath("lwff1")
				data.M.MakeMatch("lwff1", w2)
			} else {
				w2.ToFront(lwffClean, middle)
				w2.ToRuleFront(0)
				w2.AddWeight(2)
				w2.AddPath("lwff1")
				SplitRecursive(w2)
			}
		}
	}

	// Process lwffFuzzyList
	for _, lwffFuzzy := range lwffFuzzyList {

		wordA := lwffFuzzy
		wordB := w.RemainderAfter(lwffFuzzy)

		if len(wordA) > data.L.LwFuzzyMinLen && len(wordB) > data.L.LwFuzzyMinLen {

			wordALasLetter := wordA[len(wordA)-1:]
			wordBFirstLetter := wordB[:1]

			// Iterate through all the sandhi rules to find matches
			for _, sr := range data.G.SandhiRules {
				if t.RunesEqual(wordALasLetter, sr.ChA) && t.RunesEqual(wordBFirstLetter, sr.ChB) {

					// replace first and last letters with sandhi rules' letters
					word1 := t.RunesPlus(wordA[:(len(wordA)-1)], sr.Ch1)
					word2 := t.RunesPlus(sr.Ch2, wordB[1:])

					if data.G.IsInInflections(word1) {
						if data.G.IsInInflections(word2) {
							// add to matches
							w2 := w.MakeCopy()
							w2.ToFront(word1, word2)
							w2.ToRuleFront(sr.Index)
							w2.AddWeight(sr.Weight)
							w2.AddPath("lwff2")
							data.M.MakeMatch("lwff2", w2)

						} else {
							// recurse
							w2 := w.MakeCopy()
							w2.ToFront(word1, word2)
							w2.ToRuleFront(sr.Index)
							w2.AddWeight(sr.Weight)
							w2.AddPath("lwff2")
							SplitRecursive(w2)
						}
					}
				}
			}
		}
	}
}
