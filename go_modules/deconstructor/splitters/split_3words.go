package splitters

import (
	"dpd/go_modules/deconstructor/data"
	"dpd/go_modules/tools"
)

/*
Three Word Sandhi Splitter
 1. Split into three words
 2. Apply sandhi rules
 3. Update matches
*/
func Split3(w data.WordData) {

	if len(w.Middle) <= 3 {
		return
	}

	w.InitNewSplitter()
	data.M.ProcessPlusOne(w)
	word := w.Middle

	// Split the words into three parts,
	// every part containing at least one letter.
	for a := range len(word) - 2 {
		wordA := word[:a+1]

		for b := range len(word) - a - 2 {
			wordB := word[a+1 : a+b+2]
			wordC := word[a+b+2:]

			// test if all three are a match
			if data.G.IsInInflections(wordA) &&
				data.G.IsInInflections(wordB) &&
				data.G.IsInInflections(wordC) {

				w2 := w.MakeCopy()
				w2.ToFront(wordA, wordB)
				w2.ToBack(wordB, wordC)
				w2.ToRuleFront(0)
				w2.ToRuleBack(0)
				w2.AddWeight(2)
				w2.AddPath("3.1")
				w2.ProcessCount++
				data.M.MakeMatch("3.1", w2)
				continue
			}

			// test if wordA is a match but wordB is not
			// make a copy and send to Splitter2
			if data.G.IsInInflections(wordA) &&
				!data.G.IsInInflections(wordB) {

				w2 := w.MakeCopy()
				middle := tools.RunesPlus(wordB, wordC)
				w2.ToFront(wordA, middle)
				w2.ToRuleFront(0)
				w2.AddWeight(2)
				w2.AddPath("3.2")
				Split2(w2)
			}

			// test if wordC is a match but word B is not
			if data.G.IsInInflections(wordC) &&
				!data.G.IsInInflections(wordB) {

				w2 := w.MakeCopy()
				middle := tools.RunesPlus(wordA, wordB)
				w2.ToBack(middle, wordC)
				w2.ToRuleBack(0)
				w2.AddWeight(2)
				w2.AddPath("3.3")
				Split2(w2)
			}

			wordALastLetter := wordA[len(wordA)-1:]
			wordBFirstLetter := wordB[:1]
			wordBLastLetter := wordB[len(wordB)-1:]
			wordCFirstLetter := wordC[:1]

			// sandhi rules A
			for _, srA := range data.G.SandhiRules {

				if tools.RunesEqual(wordALastLetter, srA.ChA) &&
					tools.RunesEqual(wordBFirstLetter, srA.ChB) {

					word1 := tools.RunesPlus(wordA[:len(wordA)-1], srA.Ch1)
					word2 := tools.RunesPlus(srA.Ch2, wordB[1:])

					// TODO !TEST WHETHER THIS IS TRUE!
					// there's no point continuing if the words don't actually exist
					// if data.G.IsInInflectionNoFirst(word1) &&
					// 	g.IsInInflectionNoFirst(word2) {

					for _, srB := range data.G.SandhiRules {
						if tools.RunesEqual(wordBLastLetter, srB.ChA) &&
							tools.RunesEqual(wordCFirstLetter, srB.ChB) {

							var word2x []rune // wordB with first and last letters changes
							if len(word2) > 0 {
								word2x = tools.RunesPlus(word2[:len(word2)-1], srB.Ch1)
							}

							word3 := tools.RunesPlus(srB.Ch2, wordC[1:])

							if data.G.IsInInflections(word1) &&
								data.G.IsInInflections(word2x) &&
								data.G.IsInInflections(word3) {

								w2 := w.MakeCopy()
								w2.ToFront(word1, word2x)
								w2.ToBack(word2x, word3)
								w2.ToRuleFront(srA.Index)
								w2.ToRuleBack(srB.Index)
								w2.AddWeight(srA.Weight + srB.Weight)
								w2.AddPath("3.4")
								w2.ProcessCount++
								data.M.MakeMatch("3.4", w2)
							}

						}
					}
				}
			}
		}
	}
}
