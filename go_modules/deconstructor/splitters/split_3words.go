package splitters

import (
	"dpd/go_modules/deconstructor/data"
	"unicode/utf8"
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
	w.Acc.ProcessPlusOne(w)
	word := w.Middle

	// Build the middle once as a string plus a rune->byte offset table so the
	// split loops can take zero-allocation substrings instead of converting a
	// []rune candidate to string on every position.
	s := string(word)
	off := runeOffsets(s)
	n := len(word)

	// Split the words into three parts,
	// every part containing at least one letter.
	for a := range n - 2 {
		sA := s[:off[a+1]]

		for b := range n - a - 2 {
			bEnd := off[a+b+2]
			sB := s[off[a+1]:bEnd]
			sC := s[bEnd:]

			// test if all three are a match
			if data.G.IsInInflectionsStr(sA) &&
				data.G.IsInInflectionsStr(sB) &&
				data.G.IsInInflectionsStr(sC) {

				rB := []rune(sB)
				w2 := w.MakeCopy()
				w2.ToFront([]rune(sA), rB)
				w2.ToBack(rB, []rune(sC))
				w2.ToRuleFront(0)
				w2.ToRuleBack(0)
				w2.AddWeight(2)
				w2.AddPath("3.1")
				w2.ProcessCount++
				w.Acc.MakeMatch("3.1", w2)
				continue
			}

			// test if wordA is a match but wordB is not
			// make a copy and send to Splitter2
			if data.G.IsInInflectionsStr(sA) &&
				!data.G.IsInInflectionsStr(sB) {

				w2 := w.MakeCopy()
				w2.ToFront([]rune(sA), []rune(s[off[a+1]:]))
				w2.ToRuleFront(0)
				w2.AddWeight(2)
				w2.AddPath("3.2")
				Split2(w2)
			}

			// test if wordC is a match but word B is not
			if data.G.IsInInflectionsStr(sC) &&
				!data.G.IsInInflectionsStr(sB) {

				w2 := w.MakeCopy()
				w2.ToBack([]rune(s[:bEnd]), []rune(sC))
				w2.ToRuleBack(0)
				w2.AddWeight(2)
				w2.AddPath("3.3")
				Split2(w2)
			}

			wordALastRune := word[a]
			wordBFirstRune := word[a+1]
			wordBLastRune := word[a+b+1]
			wordCFirstRune := word[a+b+2]

			// O(k) index lookup: returns only rules matching this rune pair (~1-5),
			// replacing a full scan of all ~300 sandhi rules per split position.
			for _, srA := range data.G.SandhiRuleIndex[wordALastRune][wordBFirstRune] {

				word1 := s[:off[a]] + srA.Ch1S
				word2 := srA.Ch2S + s[off[a+2]:bEnd]

				// TODO !TEST WHETHER THIS IS TRUE!
				// there's no point continuing if the words don't actually exist
				// if data.G.IsInInflectionNoFirst(word1) &&
				// 	g.IsInInflectionNoFirst(word2) {

				for _, srB := range data.G.SandhiRuleIndex[wordBLastRune][wordCFirstRune] {

					var word2x string // wordB with first and last letters changes
					if len(word2) > 0 {
						_, lastSize := utf8.DecodeLastRuneInString(word2)
						word2x = word2[:len(word2)-lastSize] + srB.Ch1S
					}

					word3 := srB.Ch2S + s[off[a+b+3]:]

					if data.G.IsInInflectionsStr(word1) &&
						data.G.IsInInflectionsStr(word2x) &&
						data.G.IsInInflectionsStr(word3) {

						rWord2x := []rune(word2x)
						w2 := w.MakeCopy()
						w2.ToFront([]rune(word1), rWord2x)
						w2.ToBack(rWord2x, []rune(word3))
						w2.ToRuleFront(srA.Index)
						w2.ToRuleBack(srB.Index)
						w2.AddWeight(srA.Weight + srB.Weight)
						w2.AddPath("3.4")
						w2.ProcessCount++
						w.Acc.MakeMatch("3.4", w2)
					}
				}
			}
		}
	}
}
