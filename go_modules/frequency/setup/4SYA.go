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
		tools.HardCheck(err)

		for _, file := range directory {

			fileName := file.Name()
			filePath := filepath.Join(dirName, fileName)
			filePathRel, err := filepath.Rel(baseDir, filePath)
			tools.HardCheck(err)
			tools.PCounter(counter, 115, filePath)

			dataRead, err := os.ReadFile(filePath)
			tools.HardCheck(err)

			text := string(dataRead)
			textClean := tools.CleanMachine(text, "ṃ", false, "sya")
			textList := strings.Fields(textClean)
			freqMap := tools.ListCounter(textList)
			fileFreqMap[filePathRel] = freqMap
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
