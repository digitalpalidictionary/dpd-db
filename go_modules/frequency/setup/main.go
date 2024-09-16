package main

import "dpd/go_modules/tools"

// Saves a JSON of
//
// 1. word frequency in every individual file of CST, SC & BJT
//
//	{
//		"abh01a.att": {
//		"abbhantaramhi": 2,
//		"abbhantaraṭṭhena": 1,
//	...
//
// 2. word frequency in CST, SC & BJT,
//
// 3. every word in CST, SC & BJT
func main() {
	tools.PTitle("saving frequency files and word lists")

	tic := tools.Tic()

	makeCstFreq()
	makeScFreq()
	makeBjtFreq()
	makeSyaFreq()

	tic.Toc()
}
