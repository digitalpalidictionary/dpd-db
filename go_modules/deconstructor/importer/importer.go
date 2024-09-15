package importer

import (
	"dpd/go_modules/deconstructor/data"
	"fmt"
)

var pl = fmt.Println
var pf = fmt.Printf

type DeconImports struct {
	MatchItemList         []data.MatchItem
	SandhiRules           []data.SandhiRules
	AllInflections        map[string]string
	AllInflectionsNoFirst map[string]string
	AllInflectionsNoLast  map[string]string
	Unmatched1            map[string]string
	Unmatched2            map[string]string
}

func DeconImporter() DeconImports {
	pl("data imports")
	di := DeconImports{}

	di.MatchItemList = makeMatchItems()
	di.SandhiRules = makeSandhiRules()

	MakeUnmatched()

	di.AllInflections = ic.allInflections
	di.AllInflectionsNoFirst = ic.allInflectionsNoFirst
	di.AllInflectionsNoLast = ic.allInflectionsNoLast
	di.Unmatched1 = ic.unmatched1
	di.Unmatched2 = ic.unmatched2
	return di
}
