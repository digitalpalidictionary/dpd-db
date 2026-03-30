package data

type SandhiRules struct {
	Index  int
	ChA    []rune
	ChB    []rune
	Ch1    []rune
	Ch2    []rune
	Eg     []rune
	Weight int
}

// BuildSandhiRuleIndex groups rules into a two-level map keyed by
// (ChA[0], ChB[0]) so splitters can do O(k) lookups instead of
// iterating the full rule slice. Rules where ChA or ChB are not
// exactly 1 rune are skipped (none exist in practice).
func BuildSandhiRuleIndex(rules []SandhiRules) map[rune]map[rune][]SandhiRules {
	index := make(map[rune]map[rune][]SandhiRules)
	for _, sr := range rules {
		if len(sr.ChA) != 1 || len(sr.ChB) != 1 {
			continue
		}
		runeA := sr.ChA[0]
		runeB := sr.ChB[0]
		if index[runeA] == nil {
			index[runeA] = make(map[rune][]SandhiRules)
		}
		index[runeA][runeB] = append(index[runeA][runeB], sr)
	}
	return index
}
