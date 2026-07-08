package splitters

import (
	"dpd/go_modules/deconstructor/data"
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
	w.Acc.ProcessPlusOne(w)
	word := w.Middle

	// Build the middle once as a string plus a rune->byte offset table so the
	// split loop can take zero-allocation substrings instead of converting a
	// []rune candidate to string on every position.
	s := string(word)
	off := runeOffsets(s)
	n := len(word)

	// split the words into two parts
	for x := range n - 1 {
		aEnd := off[x+1]
		sA := s[:aEnd]
		sB := s[aEnd:]

		// check if wordA & wordB are matches
		if data.G.IsInInflectionsStr(sA) &&
			data.G.IsInInflectionsStr(sB) {

			// add to matches
			w2 := w.MakeCopy()
			w2.ToFront([]rune(sA), []rune(sB))
			w2.ToRuleFront(0)
			w2.AddWeight(2)
			w2.AddPath("2.1")
			w.Acc.MakeMatch("2.1", w2)
		}

		wordALastRune := word[x]
		wordBFirstRune := word[x+1]

		// O(k) index lookup: returns only rules matching this rune pair (~1-5),
		// replacing a full scan of all ~300 sandhi rules per split position.
		for _, sr := range data.G.SandhiRuleIndex[wordALastRune][wordBFirstRune] {

			// replace first and last letters with sandhi rules' letters
			word1 := s[:off[x]] + sr.Ch1S
			word2 := sr.Ch2S + s[off[x+2]:]

			// check if Word1 and Word2 are matches
			if data.G.IsInInflectionsStr(word1) &&
				data.G.IsInInflectionsStr(word2) {

				// add to matches
				w2 := w.MakeCopy()
				w2.ToFront([]rune(word1), []rune(word2))
				w2.ToRuleFront(sr.Index)
				w2.AddWeight(sr.Weight)
				w2.AddPath("2.2")
				w.Acc.MakeMatch("2.2", w2)
			}
		}
	}
}
