package data

import (
	"slices"
	"testing"
)

// TestMakeCopyDeepCopiesRuleSlices ensures MakeCopy clones both RuleFront and
// RuleBack, so mutating a copy never bleeds back into the original (or vice
// versa). This guards the copy-paste bug where RuleBack was never cloned.
func TestMakeCopyDeepCopiesRuleSlices(t *testing.T) {
	w := WordData{
		RuleFront: []int{1, 2},
		RuleBack:  []int{3, 4},
	}

	w2 := w.MakeCopy()

	if !slices.Equal(w2.RuleFront, w.RuleFront) {
		t.Fatalf("RuleFront not copied: got %v want %v", w2.RuleFront, w.RuleFront)
	}
	if !slices.Equal(w2.RuleBack, w.RuleBack) {
		t.Fatalf("RuleBack not copied: got %v want %v", w2.RuleBack, w.RuleBack)
	}

	w2.RuleFront[0] = 99
	w2.RuleBack[0] = 99
	if w.RuleFront[0] == 99 {
		t.Error("mutating copy RuleFront changed original (shared backing array)")
	}
	if w.RuleBack[0] == 99 {
		t.Error("mutating copy RuleBack changed original (shared backing array)")
	}
}
