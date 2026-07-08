package splitters

import "testing"

// TestRuneOffsetsMultiByte verifies that substring slicing via runeOffsets is
// byte-identical to converting a []rune sub-slice to string, for words with
// multi-byte Pāḷi characters (ā, ī, ū, ṃ, ñ, ṭ, ...). This is the invariant the
// Split2/Split3 rewrite relies on to stay correct.
func TestRuneOffsetsMultiByte(t *testing.T) {
	words := []string{
		"bhikkhūnaṃ",
		"ñāṇadassana",
		"acchakokataracchakā",
		"saṃyojanaṃ",
		"a",
		"",
	}

	for _, s := range words {
		runes := []rune(s)
		off := runeOffsets(s)

		if len(off) != len(runes)+1 {
			t.Fatalf("word %q: len(off)=%d want %d", s, len(off), len(runes)+1)
		}
		if off[len(runes)] != len(s) {
			t.Fatalf("word %q: final offset=%d want len(s)=%d", s, off[len(runes)], len(s))
		}

		for i := 0; i <= len(runes); i++ {
			for j := i; j <= len(runes); j++ {
				got := s[off[i]:off[j]]
				want := string(runes[i:j])
				if got != want {
					t.Errorf("word %q [%d:%d]: substring=%q want %q", s, i, j, got, want)
				}
			}
		}
	}
}
