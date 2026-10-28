package tools

import (
	"fmt"
	"strings"
	"testing"
)

// captureErrors returns what CleanMachine prints for the character check.
func captureErrors(t *testing.T, text string, source string) string {
	t.Helper()
	var out strings.Builder
	original := pf
	pf = func(format string, a ...any) (int, error) {
		return fmt.Fprintf(&out, format, a...)
	}
	t.Cleanup(func() { pf = original })
	CleanMachine(text, "ṃ", true, source)
	return out.String()
}

// Line 235 of Kathāsallāpasikkhā, copied from resources/other_pali_texts.
const burmeseExercise = "6.\tImaṃ pana marammabhāsaṃ pāḷibhāsāya parivattehi: “တရားတော််ကို ပူဇော်ပါ၏”ti."

func TestOtherTextsIgnoreBurmeseScript(t *testing.T) {
	if got := captureErrors(t, burmeseExercise, "other"); got != "" {
		t.Errorf("Burmese script reported as an error:\n%s", got)
	}
}

func TestOtherTextsStillReportRealErrors(t *testing.T) {
	got := captureErrors(t, burmeseExercise+" é", "other")
	if !strings.Contains(got, "U+00E9") {
		t.Errorf("expected an error for é, got:\n%q", got)
	}
	if lines := strings.Count(got, "error:"); lines != 1 {
		t.Errorf("expected exactly 1 error line, got %d:\n%s", lines, got)
	}
}

func TestOtherSourcesStillReportBurmeseScript(t *testing.T) {
	for _, source := range []string{"cst", "sc", "bjt", "sya", "dpd"} {
		if got := captureErrors(t, burmeseExercise, source); !strings.Contains(got, "U+1010") {
			t.Errorf("%s: expected Burmese script to be reported, got:\n%q", source, got)
		}
	}
}
