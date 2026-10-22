package importer

import "testing"

// TestMatchItemsFromRowsTrimsWord checks that surrounding whitespace on the
// compound is dropped, so the lookup key made from it has no outer space.
func TestMatchItemsFromRowsTrimsWord(t *testing.T) {
	rows := []map[string]string{
		{"compound": "ūsakhaṇḍaṃ ", "split": "ūsa + khaṇḍaṃ "},
		{"compound": " akkharappabhedānaṃ", "split": "akkhara + pabhedānaṃ"},
		{"compound": "sabbadhammā", "split": "sabba + dhammā"},
	}

	got := matchItemsFromRows(rows)

	want := []string{"ūsakhaṇḍaṃ", "akkharappabhedānaṃ", "sabbadhammā"}
	if len(got) != len(want) {
		t.Fatalf("expected %d match items, got %d", len(want), len(got))
	}
	for i, w := range want {
		if got[i].Word != w {
			t.Errorf("item %d: expected word %q, got %q", i, w, got[i].Word)
		}
	}
	if got[0].Split != "ūsa + khaṇḍaṃ" {
		t.Errorf("expected trimmed split, got %q", got[0].Split)
	}
}

// TestManualCorrectionWordsAreTrimmed checks that the words removed from the
// deconstructor input match the trimmed words of the manual match items.
// Otherwise a worker also deconstructs the word and its result overwrites the
// manual split.
func TestManualCorrectionWordsAreTrimmed(t *testing.T) {
	rows := []map[string]string{
		{"compound": "vinivijjhanaṭṭhenāti ", "split": "vinivijjhana + aṭṭhena + iti"},
		{"compound": " ūsakhaṇḍaṃ", "split": "ūsa + khaṇḍaṃ"},
		{"compound": "sabbadhammā", "split": "sabba + dhammā"},
	}

	got := manualCorrectionWordsFromRows(rows)

	for _, item := range matchItemsFromRows(rows) {
		if _, ok := got[item.Word]; !ok {
			t.Errorf("manual match item word %q is not excluded from the input", item.Word)
		}
	}
	if len(got) != 3 {
		t.Errorf("expected 3 words, got %d: %v", len(got), got)
	}
}
