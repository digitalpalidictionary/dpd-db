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
	tools.PGreenTitle("Save word frequency in CST to JSON")

	dirName := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.CstTxtTextDir,
	)

	directory, err := os.ReadDir(dirName)
	tools.HardCheck(err)

	fileFreqMap := map[string]map[string]int{}
	for i, dirEntry := range directory {

		fileName := dirEntry.Name()
		fileNameClean, _ := strings.CutSuffix(fileName, ".txt")
		fileNameClean = fileNameClean + ".xml"
		filePath := filepath.Join(dirName, fileName)

		tools.PCounter(i+1, len(directory), filePath)

		dataRead, err := os.ReadFile(filePath)
		tools.HardCheck(err)

		text := string(dataRead)
		textClean := tools.CleanMachine(text, "ṃ", true, "cst")
		textList := strings.Fields(textClean)
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
	tools.PGreen("saving file freq json")

	ok := tools.SaveJson(filePath, fileFreqMap)
	if ok {
		tools.POk(len(fileFreqMap))
	} else {
		tools.PRed("error while saving")
	}
}

func makeFreqMap(fileFreqMap map[string]map[string]int) map[string]int {
	tools.PGreen("making freq map")
	freqMap := map[string]int{}

	for _, FreqMap := range fileFreqMap {
		for word, freq := range FreqMap {
			freqMap[word] = freqMap[word] + freq
		}
	}
	tools.POk(len(freqMap))
	return freqMap
}

func saveFreqMap(filePath string, FreqMap map[string]int) {
	tools.PGreen("saving freq json ")
	ok := tools.SaveJson(filePath, FreqMap)
	if ok {
		tools.POk(len(FreqMap))
	} else {
		tools.PRed("error while saving")
	}
}

func makeWordList(cstFreqMap map[string]int) []string {
	tools.PGreen("making wordlist ")
	WordList := []string{}
	for word := range cstFreqMap {
		WordList = append(WordList, word)
	}
	tools.POk(len(WordList))
	return WordList
}

func saveWordList(filePath string, cstWordList []string) {
	tools.PGreen("saving wordlist json ")

	ok := tools.SaveJson(filePath, cstWordList)
	if ok {
		tools.POk(len(cstWordList))
	} else {
		tools.PRed("error while saving")
	}
}
