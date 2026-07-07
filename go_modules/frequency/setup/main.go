package main

import (
	"dpd/go_modules/tools"
	"fmt"
	"os"
)

// Saves a JSON of
//
// 1. word frequency in every individual file of CST, SC, BJT & SYA
//
//	{
//		"abh01a.att": {
//		"abbhantaramhi": 2,
//		"abbhantaraṭṭhena": 1,
//	...
//
// 2. word frequency in CST, SC, BJT & SYA,
//
// 3. every word in CST, SC, BJT & SYA
//
// Usage:
//
//	go run ./go_modules/frequency/setup          # all four corpora
//	go run ./go_modules/frequency/setup sya      # one corpus only
func main() {
	tools.PTitle("saving frequency files and word lists")

	tic := tools.Tic()

	corpora := map[string]func(){
		"cst": makeCstFreq,
		"sc":  makeScFreq,
		"bjt": makeBjtFreq,
		"sya": makeSyaFreq,
	}

	if len(os.Args) > 1 {
		name := os.Args[1]
		makeFreq, ok := corpora[name]
		if !ok {
			fmt.Printf("unknown corpus %q (want cst, sc, bjt or sya)\n", name)
			os.Exit(1)
		}
		makeFreq()
	} else {
		makeCstFreq()
		makeScFreq()
		makeBjtFreq()
		makeSyaFreq()
	}

	tic.Toc()
}
