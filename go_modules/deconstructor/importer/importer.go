package importer

import (
	"dpd/go_modules/deconstructor/data"
	"dpd/go_modules/tools"
	"fmt"
	"sync"
)

var pl = fmt.Println
var pf = fmt.Printf

type DeconImports struct {
	MatchItemList         []data.MatchItem
	SandhiRuleIndex       map[rune]map[rune][]data.SandhiRules
	AllInflections        map[string]string
	AllInflectionsNoFirst map[string]string
	AllInflectionsNoLast  map[string]string
	Unmatched1            map[string]string
	Unmatched2            map[string]string
}

func DeconImporter() DeconImports {
	tools.PGreenTitle("importing data")

	var matchItemList []data.MatchItem
	var sandhiRules []data.SandhiRules

	var wg sync.WaitGroup
	wg.Add(3)
	go func() { defer wg.Done(); matchItemList = makeMatchItems() }()
	go func() { defer wg.Done(); sandhiRules = makeSandhiRules() }()
	go func() { defer wg.Done(); MakeUnmatched() }()
	wg.Wait()

	return DeconImports{
		MatchItemList:         matchItemList,
		SandhiRuleIndex:       data.BuildSandhiRuleIndex(sandhiRules),
		AllInflections:        ic.allInflections,
		AllInflectionsNoFirst: ic.allInflectionsNoFirst,
		AllInflectionsNoLast:  ic.allInflectionsNoLast,
		Unmatched1:            ic.unmatched1,
		Unmatched2:            ic.unmatched2,
	}
}
