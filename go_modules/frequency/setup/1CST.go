package main

import (
	"dpd/go_modules/tools"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

var pl = fmt.Println
var pf = fmt.Printf

func makeCstFreq() {
	pl("Save word frequency in cst to JSON")

	dirName := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.CstTxtTextDir,
	)

	directory, err := os.ReadDir(dirName)
	tools.Check(err)

	fileFreqMap := map[string]map[string]int{}
	for i, dirEntry := range directory {

		fileName := dirEntry.Name()
		fileNameClean, _ := strings.CutSuffix(fileName, ".txt")
		fileNameClean = fileNameClean + ".xml"
		filePath := filepath.Join(dirName, fileName)

		pf("%v / %v %v\n", i+1, len(directory), filePath)

		dataRead, err := os.ReadFile(filePath)
		tools.Check(err)

		text := string(dataRead)
		textClean := tools.CleanMachine(text, "ṃ", true, "cst")
		textList := strings.Split(textClean, " ")
		freqMap := tools.ListCounter(textList)
		fileFreqMap[fileNameClean] = freqMap
	}

	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.CstFileFreqMap,
	)
	saveFileFreqMap(filePath, fileFreqMap)

	freqMap := makeFreqMap(fileFreqMap)
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.CstFreqMap,
	)
	saveFreqMap(filePath, freqMap)

	WordList := makeWordList(freqMap)
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.CstWordList,
	)
	saveWordList(filePath, WordList)

}

func saveFileFreqMap(filePath string, fileFreqMap map[string]map[string]int) {
	pf("saving file freq json ")

	ok := tools.SaveJson(filePath, fileFreqMap)
	if ok {
		pf("%v ok\n", len(fileFreqMap))
	}
}

func makeFreqMap(fileFreqMap map[string]map[string]int) map[string]int {
	pf("making freq map ")
	freqMap := map[string]int{}

	for _, FreqMap := range fileFreqMap {
		for word, freq := range FreqMap {
			freqMap[word] = freqMap[word] + freq
		}
	}
	pl(len(freqMap))
	return freqMap
}

func saveFreqMap(filePath string, FreqMap map[string]int) {
	pf("saving freq json ")
	ok := tools.SaveJson(filePath, FreqMap)
	if ok {
		pf("%v ok\n", len(FreqMap))
	}
}

func makeWordList(cstFreqMap map[string]int) []string {
	pf("making wordlist ")
	WordList := []string{}
	for word := range cstFreqMap {
		WordList = append(WordList, word)
	}
	pf("%v\n", len(WordList))
	return WordList
}

func saveWordList(filePath string, cstWordList []string) {
	pf("saving wordlist json ")

	ok := tools.SaveJson(filePath, cstWordList)
	if ok {
		pf("%v ok\n", len(cstWordList))
	}
}
