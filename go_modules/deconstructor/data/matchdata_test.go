package data

import (
	"reflect"
	"testing"
)

// selectTopEntries keeps only the lowest-ProcessCount candidates (the sort makes
// the first item the minimum) up to the limit, reproducing the original global
// SaveTopEntriesJson rule per word.
func TestSelectTopEntriesKeepsMinProcessCount(t *testing.T) {
	items := []MatchItem{
		{Word: "w", Split: "a", ProcessCount: 1},
		{Word: "w", Split: "b", ProcessCount: 1},
		{Word: "w", Split: "c", ProcessCount: 2},
		{Word: "w", Split: "d", ProcessCount: 3},
	}
	got := selectTopEntries(items, 5)
	want := []string{"a", "b"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v, want %v", got, want)
	}
}

func TestSelectTopEntriesRespectsLimit(t *testing.T) {
	items := []MatchItem{
		{Word: "w", Split: "a", ProcessCount: 1},
		{Word: "w", Split: "b", ProcessCount: 1},
		{Word: "w", Split: "c", ProcessCount: 1},
		{Word: "w", Split: "d", ProcessCount: 1},
		{Word: "w", Split: "e", ProcessCount: 1},
		{Word: "w", Split: "f", ProcessCount: 1},
	}
	got := selectTopEntries(items, 5)
	if len(got) != 5 {
		t.Fatalf("expected 5 entries, got %d (%v)", len(got), got)
	}
}

func TestSelectTopEntriesSkipsDuplicateSplit(t *testing.T) {
	items := []MatchItem{
		{Word: "w", Split: "a", ProcessCount: 1},
		{Word: "w", Split: "a", ProcessCount: 1},
		{Word: "w", Split: "b", ProcessCount: 1},
	}
	got := selectTopEntries(items, 5)
	want := []string{"a", "b"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v, want %v", got, want)
	}
}

// compareMatchItems must be a total order: Word, then ProcessCount, then Weight,
// then SplitRatio, then Split text as the final deterministic tiebreak.
func TestCompareMatchItemsTotalOrder(t *testing.T) {
	// Equal on all ranking keys except split text -> ordered by split text.
	a := MatchItem{Word: "w", ProcessCount: 1, Weight: 1, SplitRatio: 1, Split: "x + y"}
	b := MatchItem{Word: "w", ProcessCount: 1, Weight: 1, SplitRatio: 1, Split: "x + z"}
	if compareMatchItems(a, b) >= 0 {
		t.Fatalf("expected a < b by split-text tiebreak")
	}
	// ProcessCount dominates weight.
	c := MatchItem{Word: "w", ProcessCount: 1, Weight: 9}
	d := MatchItem{Word: "w", ProcessCount: 2, Weight: 0}
	if compareMatchItems(c, d) >= 0 {
		t.Fatalf("expected lower ProcessCount to sort first")
	}
}

// FinishWord groups a mixed buffer by word (as can happen if a phantom word is
// produced alongside the real one) and selects each word's top-5 independently.
func TestFinishWordGroupsByWord(t *testing.T) {
	m := NewMatchData()
	m.wordBuf = []MatchItem{
		{Word: "beta", Split: "b1", ProcessCount: 1},
		{Word: "alpha", Split: "a2", ProcessCount: 2},
		{Word: "alpha", Split: "a1", ProcessCount: 1},
		{Word: "beta", Split: "b2", ProcessCount: 1},
	}
	m.FinishWord()

	if got, want := m.topDict["alpha"], []string{"a1"}; !reflect.DeepEqual(got, want) {
		t.Fatalf("alpha: got %v, want %v", got, want)
	}
	if got, want := m.topDict["beta"], []string{"b1", "b2"}; !reflect.DeepEqual(got, want) {
		t.Fatalf("beta: got %v, want %v", got, want)
	}
	if len(m.wordBuf) != 0 {
		t.Fatalf("wordBuf not cleared after FinishWord: %v", m.wordBuf)
	}
}
