package data

import "testing"

// TestIsInInflectionsStrMatchesRune ensures the string-keyed lookup used by the
// Split2/Split3 hot loops returns the same result as the []rune form for every
// case, including multi-byte Pāḷi words and the empty string.
func TestIsInInflectionsStrMatchesRune(t *testing.T) {
	g := GlobalData{
		AllInflections: map[string]string{
			"gacchati":   "",
			"bhikkhūnaṃ": "",
			"ñāṇa":       "",
		},
	}

	cases := []string{"gacchati", "bhikkhūnaṃ", "ñāṇa", "gacchat", "", "xyz"}
	for _, s := range cases {
		want := g.IsInInflections([]rune(s))
		got := g.IsInInflectionsStr(s)
		if got != want {
			t.Errorf("word %q: IsInInflectionsStr=%v IsInInflections=%v", s, got, want)
		}
	}
}
