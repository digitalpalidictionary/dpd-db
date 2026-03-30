package data_test

import (
	"dpd/go_modules/deconstructor/data"
	"testing"
)

func makeSampleRules() []data.SandhiRules {
	return []data.SandhiRules{
		{Index: 1, ChA: []rune("a"), ChB: []rune("p"), Ch1: []rune("a"), Ch2: []rune("ap"), Weight: 3},
		{Index: 2, ChA: []rune("ā"), ChB: []rune("p"), Ch1: []rune("a"), Ch2: []rune("ap"), Weight: 3},
		{Index: 3, ChA: []rune("ā"), ChB: []rune("p"), Ch1: []rune("ā"), Ch2: []rune("ap"), Weight: 3},
		{Index: 4, ChA: []rune("a"), ChB: []rune("t"), Ch1: []rune("a"), Ch2: []rune(""), Weight: 2},
	}
}

// Index must have exactly 2 distinct runeA keys (a and ā).
func TestBuildSandhiRuleIndex_DistinctRuneAKeys(t *testing.T) {
	index := data.BuildSandhiRuleIndex(makeSampleRules())
	if len(index) != 2 {
		t.Errorf("expected 2 runeA groups, got %d", len(index))
	}
}

// A known (runeA, runeB) pair must resolve to the correct rule.
func TestBuildSandhiRuleIndex_LookupReturnsMatchingRule(t *testing.T) {
	index := data.BuildSandhiRuleIndex(makeSampleRules())

	aRune := rune('a')
	pRune := rune('p')

	rules := index[aRune][pRune]
	if len(rules) != 1 {
		t.Fatalf("expected 1 rule for (a, p), got %d", len(rules))
	}
	if rules[0].Index != 1 {
		t.Errorf("expected rule index 1, got %d", rules[0].Index)
	}
}

// Multiple rules sharing the same (runeA, runeB) key must all be present.
func TestBuildSandhiRuleIndex_MultipleRulesForSameKey(t *testing.T) {
	index := data.BuildSandhiRuleIndex(makeSampleRules())

	āRune := []rune("ā")[0]
	pRune := rune('p')

	rules := index[āRune][pRune]
	if len(rules) != 2 {
		t.Errorf("expected 2 rules for (ā, p), got %d", len(rules))
	}
}

// An absent runeA key must return nil (safe to double-index into without panic).
func TestBuildSandhiRuleIndex_UnknownKeyReturnsNil(t *testing.T) {
	index := data.BuildSandhiRuleIndex(makeSampleRules())

	xRune := rune('x')
	rules := index[xRune][rune('y')]
	if rules != nil {
		t.Errorf("expected nil for unknown key, got %v", rules)
	}
}

// Ranging over an absent key must not panic and must yield zero iterations.
func TestBuildSandhiRuleIndex_RangeOverAbsentKeyIsSafe(t *testing.T) {
	index := data.BuildSandhiRuleIndex(makeSampleRules())

	count := 0
	for range index[rune('z')][rune('z')] {
		count++
	}
	if count != 0 {
		t.Errorf("expected 0 iterations for absent key, got %d", count)
	}
}
