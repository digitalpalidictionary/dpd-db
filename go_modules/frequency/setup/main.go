package main

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
	makeCstFreq()
	makeScFreq()
	makeBjtFreq()
	makeSyaFreq()
}
