package main

import (
	"fmt"
	"gm/deconstructor/importer"
	"gm/tools"
)

var pl = fmt.Println

func main() {
	n := importer.DeconImporter()
	o := importer.DeconImporterOld()

	x := tools.MapDifference[string](n.AllInflections, o.AllInflections)
	// x = tools.MapDifference[string](n.AllInflectionsNoLast, o.AllInflectionsNoLast)
	x = tools.MapDifference[string](n.Unmatched1, o.Unmatched1)
	x = tools.MapDifference[string](o.Unmatched1, n.Unmatched1)
	pl(x)
	pl(len(x))

	pl(&n.Unmatched1 == &n.Unmatched2)
	pl(&o.Unmatched1 == &o.Unmatched2)
	// counter := 0
	// for k, v := range n.Unmatched1 {
	// 	if tools.StrLen(k) <= 3 {
	// 		pl(k, v)
	// 		counter++
	// 	}
	// }
	// pl(counter)
}
