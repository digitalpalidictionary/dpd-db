package splitters

import (
	"dpd/go_modules/deconstructor/data"
	t "dpd/go_modules/tools"
)

func SplitLwfb(w data.WordData) {

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

	lwfbCleanList := [][]rune{}
	lwfbFuzzyList := [][]rune{}

	for i := range len(word) {
		// lwfb := word[len(word)-i-1 : len(word)-1]
		lwfb := word[i:]

		if data.G.IsInInflections(lwfb) {
			lwfbCleanList = append(lwfbCleanList, lwfb)
		}

		if data.G.IsInInflectionNoFirst(lwfb) {
			lwfbFuzzyList = append(lwfbFuzzyList, lwfb)
		}
	}

	// Limit the size of the lists if not the first process
	if w.ProcessCount != 0 {
		if len(lwfbCleanList) >= data.L.LwCleanListMaxLen &&
			data.L.LwCleanListMaxLen != 0 {
			lwfbCleanList = lwfbCleanList[:data.L.LwCleanListMaxLen]
		}
		if len(lwfbFuzzyList) >= data.L.LwFuzzyListMaxLen &&
			data.L.LwFuzzyListMaxLen != 0 {
			lwfbFuzzyList = lwfbFuzzyList[:data.L.LwFuzzyListMaxLen]
		}
	}

	// Process lwfbCleanList
	for _, lwfbClean := range lwfbCleanList {
		w2 := w.MakeCopy()
		middle := w2.RemainderBefore(lwfbClean)

		if len(middle) >= data.L.LwCleanMinLen {
			if data.G.IsInInflections(middle) {
				w2.ToBack(middle, lwfbClean)
				w2.ToRuleFront(0)
				w2.AddWeight(2)
				w2.AddPath("lwfb1")
				data.M.MakeMatch("lwfb1", w2)
			} else {
				w2.ToBack(middle, lwfbClean)
				w2.ToRuleFront(0)
				w2.AddWeight(2)
				w2.AddPath("lwfb1")
				SplitRecursive(w2)
			}
		}
	}

	// Process lwfbFuzzyList
	for _, lwfbFuzzy := range lwfbFuzzyList {

		wordA := w.RemainderBefore(lwfbFuzzy)
		wordB := lwfbFuzzy

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
							w2.ToBack(word1, word2)
							w2.ToRuleBack(sr.Index)
							w2.AddWeight(sr.Weight)
							w2.AddPath("lwfb2")
							data.M.MakeMatch("lwfb2", w2)

						} else {
							// recurse
							w2 := w.MakeCopy()
							w2.ToBack(word1, word2)
							w2.ToRuleBack(sr.Index)
							w2.AddWeight(sr.Weight)
							w2.AddPath("lwfb2")
							SplitRecursive(w2)
						}
					}
				}
			}
		}
	}
}
