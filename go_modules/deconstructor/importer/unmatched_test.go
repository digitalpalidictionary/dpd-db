package importer

import "testing"

// TestCstAbbreviationsFromRows checks that only CST-source rows are kept, that
// surrounding whitespace (CRLF line endings leave a trailing \r) is trimmed,
// and that empty abbreviations are skipped.
func TestCstAbbreviationsFromRows(t *testing.T) {
	rows := []map[string]string{
		{"source": "CST", "abbreviation": "sī", "meaning": "Sīhaḷa"},
		{"source": "CST", "abbreviation": "syā", "meaning": "Syām"},
		{"source": "CST", "abbreviation": "ni\r", "meaning": "Nikāya"}, // CRLF residue
		{"source": "PTS", "abbreviation": "DN", "meaning": "Dīgha-Nikāya"},
		{"source": "Cone", "abbreviation": "Aś", "meaning": "Aśokan"},
		{"source": "CST", "abbreviation": "", "meaning": "empty"},
	}

	got := cstAbbreviationsFromRows(rows)

	for _, want := range []string{"sī", "syā", "ni"} {
		if _, ok := got[want]; !ok {
			t.Errorf("expected CST abbreviation %q to be included", want)
		}
	}
	for _, notWanted := range []string{"DN", "Aś", "", "ni\r"} {
		if _, ok := got[notWanted]; ok {
			t.Errorf("did not expect %q to be included", notWanted)
		}
	}
	if len(got) != 3 {
		t.Errorf("expected 3 CST abbreviations, got %d: %v", len(got), got)
	}
}
