package data

import (
	"fmt"
	"slices"
	"strings"
	"time"
)

var W = WordData{}

/*
TODO update this into docs
Word data with a history of the current word's journey

	word 		: The initial word to be split
	count 		: The number of processes
	front 		: The front portion of the split
	middle 		: The remaining middle portion of the split
	back 		: The back part of the split
	tried 		: List of tried, unsuccessful split options
	matchFlag 	: word has been matches successfully
	path 		: route the word has taken on its journey
	startTime 	: When did the words processing start?
	------------------------
*/
type WordData struct {
	Word         []rune
	ProcessCount int
	MatchFlag    bool
	RecurseFlag  bool
	LwffLwfbFlag bool
	Front        []string
	Middle       []rune
	Back         []string
	RuleFront    []string
	RuleBack     []string
	Weight       int
	Path         []string
	StartTime    time.Time
	TimeDuration time.Duration
}

// Copy a word's data into new memory, not to mess with for loops
func (w WordData) MakeCopy() WordData {
	w2 := WordData{}
	w2.Word = append(w2.Word, w.Word...)
	w2.ProcessCount = w.ProcessCount + 0
	w2.MatchFlag = w.MatchFlag
	w2.RecurseFlag = w.RecurseFlag
	w2.LwffLwfbFlag = w.LwffLwfbFlag
	w2.Front = []string{}
	w2.Front = append(w2.Front, w.Front...)
	w2.Middle = []rune{}
	w2.Middle = append(w2.Middle, w.Middle...)
	w2.Back = []string{}
	w2.Back = append(w2.Back, w.Back...)
	w2.RuleFront = []string{}
	w2.RuleFront = append(w2.RuleFront, w.RuleFront...)
	w2.RuleBack = []string{}
	w2.RuleBack = append(w2.RuleBack, w.RuleBack...)
	w2.Weight = w.Weight + 0
	w2.Path = []string{}
	w2.Path = append(w2.Path, w.Path...)
	w2.StartTime = w.StartTime
	w2.TimeDuration = w.TimeDuration
	return w2
}

// Initialize a word with some default settings
func InitWordData(word []rune) WordData {
	w := WordData{}
	w.Word = word
	w.ProcessCount = 0
	w.RecurseFlag = false
	w.Middle = word
	w.Path = []string{"start"}
	w.StartTime = time.Now()
	return w
}

// Function to run every time a word arrives at a new splitter
//  1. Updates the matchFlag to false
//  2. Updates the processName
func (w *WordData) InitNewSplitter() {
	w.MatchFlag = false
	w.ProcessCount++

}

func (w *WordData) AddPath(processName string) {
	w.Path = append(w.Path, processName)
}

// Return the list of paths joined with ' > '
func (w WordData) pathString() string {
	return strings.Join(w.Path, " > ")
}

// Return the list of rules joined with '|'
func (w WordData) ruleString() string {
	var rulesList []string
	rulesList = append(rulesList, w.RuleFront...)
	rulesList = append(rulesList, w.RuleBack...)
	return strings.Join(rulesList, "|")
}

// Append the word to the end of the w.Front list.
func (w *WordData) ToFront(front []rune, middle []rune) {
	w.Front = append(w.Front, string(front))
	w.Middle = middle
}

// Reassigns the middle, and inserts the back
// into position 0 in the w.back list
func (w *WordData) ToBack(middle []rune, back []rune) {
	w.Middle = middle
	w.Back = slices.Insert(w.Back, 0, string(back))
}

// Append the rule to the w.ruleFront list.
func (w *WordData) ToRuleFront(rule string) {
	w.RuleFront = append(w.RuleFront, rule)
}

// Insert the rule to the 0 position in the w.ruleBack list.
func (w *WordData) ToRuleBack(rule string) {
	w.RuleBack = slices.Insert(w.RuleBack, 0, rule)
}

// Check if w.Middle starts with a certain prefix.
func (w WordData) StartsWith(prefix string) bool {
	return strings.HasPrefix(string(w.Middle), prefix)
}

// Check if w.Middle ends with a certain prefix.
func (w WordData) EndsWith(suffix string) bool {
	return strings.HasSuffix(string(w.Middle), suffix)
}

// Check if w.Middle ends with amy of a list of suffixes.
func (w WordData) EndsWithList(suffixes []string) bool {
	for _, suffix := range suffixes {
		if strings.HasSuffix(string(w.Middle), suffix) {
			return true
		}
	}
	return false
}

// Check if the word has a negative prefix 'a' 'an' 'na' 'nā'
func (w WordData) HasNegPrefix() bool {

	if w.StartsWith("a") ||
		w.StartsWith("an") ||
		w.StartsWith("na") ||
		w.StartsWith("nā") {
		return true
	} else {
		return false
	}
}

// Return the RemainderAfter of the w.Middle after removing the front word
func (w WordData) RemainderAfter(front []rune) []rune {
	return w.Middle[len(front):]
}

// Return the RemainderBefore of the w.Middle after removing the back word
func (w WordData) RemainderBefore(back []rune) []rune {
	return w.Middle[:len(w.Middle)-len(back)]
}

// Check if w.Middle starts with a double letter
func (w WordData) HasInitialDouble() bool {
	if len(w.Middle) > 1 {
		if w.Middle[0] == w.Middle[1] {
			return true
		} else {
			return false
		}
	}
	return false
}

// Add weight to the word, int 3 is default.
func (w *WordData) AddWeight(weight int) {
	w.Weight = w.Weight + weight
}

// Return a w.Front middle and back separated by " + "
func (w WordData) MakeSplitString() string {
	splitList := []string{}
	for _, slice := range w.Front {
		splitList = append(splitList, string(slice))
	}
	splitList = append(splitList, string(w.Middle))
	for _, slice := range w.Back {
		splitList = append(splitList, string(slice))
	}
	return strings.Join(splitList, " + ")
}

func (w WordData) PrintSplitString() {
	fmt.Println(w.MakeSplitString())
}
