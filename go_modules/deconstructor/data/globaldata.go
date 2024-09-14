package data

var G = GlobalData{
	SandhiRules:           []SandhiRules{},
	Unmatched:             map[string]string{},
	AllInflections:        map[string]string{},
	AllInflectionsNoFirst: map[string]string{},
	AllInflectionsNoLast:  map[string]string{},
}

// Globally accessible constants

// sandhiRules : List of sandhi rules
// unmatched : All unmatched words in Pāḷi texts
// allInflections : Every inflection of every word in DPD
// allInflectionsNoFirst : Every inflections without the first letter
// allInflectionsNoLast : Every inflections without the last letter
type GlobalData struct {
	SandhiRules           []SandhiRules
	Unmatched             map[string]string
	AllInflections        map[string]string
	AllInflectionsNoFirst map[string]string
	AllInflectionsNoLast  map[string]string
}

// test if a word is in all inflections
func (g GlobalData) IsInInflections(word []rune) bool {
	_, exists := g.AllInflections[string(word)]
	return exists
}

// test if a word is in all inflections (with no first letter)
func (g GlobalData) IsInInflectionNoFirst(word []rune) bool {
	_, exists := g.AllInflectionsNoFirst[string(word)]
	return exists
}

// test if a word is in all inflections (with no last letter)
func (g GlobalData) IsInInflectionNoLast(word []rune) bool {
	_, exists := g.AllInflectionsNoLast[string(word)]
	return exists
}
