package main

import (
	"dpd/go_modules/tools"
	"os"
	"path/filepath"
	"strings"
)

func makeSyaFreq() {
	tools.PGreenTitle("Save word frequency in Thai texts to JSON")

	fileFreqMap := map[string]map[string]int{}

	baseDir := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.SyaTextDir,
	)

	folders := []string{"canon", "commentary"}

	counter := 1
	for _, folder := range folders {
		dirName := filepath.Join(baseDir, folder)

		directory, err := os.ReadDir(dirName)
		tools.Check(err)

		for _, file := range directory {

			fileName := file.Name()
			filePath := filepath.Join(dirName, fileName)
			tools.PCounter(counter, 115, filePath)

			dataRead, err := os.ReadFile(filePath)
			tools.Check(err)

			text := string(dataRead)
			textClean := tools.CleanMachine(text, "ṃ", false, "sya")
			textList := strings.Split(textClean, " ")
			freqMap := tools.ListCounter(textList)
			fileFreqMap[fileName] = freqMap
			counter++
		}
	}
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.SyaFileFreqMap,
	)
	saveFileFreqMap(filePath, fileFreqMap)

	freqMap := makeFreqMap(fileFreqMap)
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.SyaFreqMap,
	)
	saveFreqMap(filePath, freqMap)

	WordList := makeWordList(freqMap)
	filePath = filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.SyaWordList,
	)
	saveWordList(filePath, WordList)
}
