package data

var G = GlobalData{
	SandhiRuleIndex:       map[rune]map[rune][]SandhiRules{},
	Unmatched:             map[string]string{},
	AllInflections:        map[string]string{},
	AllInflectionsNoFirst: map[string]string{},
	AllInflectionsNoLast:  map[string]string{},
}

// Globally accessible constants

// sandhiRuleIndex : O(k) lookup index: runeA -> runeB -> matching rules
// unmatched : All unmatched words in Pāḷi texts
// allInflections : Every inflection of every word in DPD
// allInflectionsNoFirst : Every inflections without the first letter
// allInflectionsNoLast : Every inflections without the last letter
type GlobalData struct {
	SandhiRuleIndex       map[rune]map[rune][]SandhiRules
	Unmatched             map[string]string
	AllInflections        map[string]string
	AllInflectionsNoFirst map[string]string
	AllInflectionsNoLast  map[string]string
}

// IsInInflections reports whether word appears in the inflections set.
func (g GlobalData) IsInInflections(word []rune) bool {
	_, exists := g.AllInflections[string(word)]
	return exists
}

// IsInInflectionNoFirst reports whether word appears in the no-first-letter inflections set.
func (g GlobalData) IsInInflectionNoFirst(word []rune) bool {
	_, exists := g.AllInflectionsNoFirst[string(word)]
	return exists
}

// IsInInflectionNoLast reports whether word appears in the no-last-letter inflections set.
func (g GlobalData) IsInInflectionNoLast(word []rune) bool {
	_, exists := g.AllInflectionsNoLast[string(word)]
	return exists
}
