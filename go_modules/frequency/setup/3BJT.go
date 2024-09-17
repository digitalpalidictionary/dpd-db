package main

import (
	"dpd/go_modules/tools"
	"os"
	"path/filepath"
	"strings"
)

func makeBjtFreq() {
	tools.PGreenTitle("Save word frequency in BJT to JSON")

	dirName := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.BjtRomanTxtDir,
	)

	directory, err := os.ReadDir(dirName)
	tools.HardCheck(err)

	fileFreqMap := map[string]map[string]int{}
	for i, file := range directory {
		fileName := file.Name()
		fileNameClean := strings.TrimSuffix(fileName, ".txt")
		filePath := filepath.Join(dirName, fileName)
		tools.PCounter(i+1, len(directory), filePath)

		dataRead, err := os.ReadFile(filePath)
		tools.HardCheck(err)

		text := string(dataRead)
		textClean := tools.CleanMachine(text, "ṃ", true, "bjt")
		textList := strings.Fields(textClean)
		freqMap := tools.ListCounter(textList)
		fileFreqMap[fileNameClean] = freqMap
	}

	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.BjtFileFreqMap,
	)
	saveFileFreqMap(filePath, fileFreqMap)

	freqMap := makeFreqMap(fileFreqMap)
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.BjtFreqMap,
	)
	saveFreqMap(filePath, freqMap)

	WordList := makeWordList(freqMap)
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.BjtWordList,
	)
	saveWordList(filePath, WordList)
}

// another way to read BJT
func anotherWay() {
	filePath := "../dpd-db/resources/tipitaka.lk/public/static/roman_json/an-1.json"
	type bjtObject map[string][]map[string]map[string][]map[string]string
	bjt := bjtObject{}
	bjt = tools.ReadJsonBjt(filePath, bjt)
	pages := bjt["pages"]
	for _, page := range pages {
		entries := page["pali"]["entries"]
		for _, entry := range entries {
			text := entry["text"]
			pl(text)
		}
		footnotes := page["pali"]["footnotes"]
		for _, footnote := range footnotes {
			text := footnote["text"]
			pl(text)
		}
		tools.Pause()
	}
}
