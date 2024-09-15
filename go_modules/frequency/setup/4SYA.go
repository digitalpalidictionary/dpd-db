package main

import (
	"dpd/go_modules/tools"
	"os"
	"path/filepath"
	"strings"
)

func makeSyaFreq() {
	pl("Save word frequency in Syam to JSON")

	fileFreqMap := map[string]map[string]int{}

	baseDir := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.SyaTextDir,
	)

	folders := []string{"canon", "commentary"}

	for _, folder := range folders {
		dirName := filepath.Join(baseDir, folder)

		directory, err := os.ReadDir(dirName)
		tools.Check(err)

		for _, file := range directory {

			fileName := file.Name()
			filePath := filepath.Join(dirName, fileName)
			// pf("%v / %v %v\n", i+1, len(directory), filePath)
			pl(filepath.Rel(baseDir, filePath))

			dataRead, err := os.ReadFile(filePath)
			tools.Check(err)

			text := string(dataRead)
			textClean := tools.CleanMachine(text, "ṃ", true, "sya")
			textList := strings.Split(textClean, " ")
			freqMap := tools.ListCounter(textList)
			fileFreqMap[fileName] = freqMap
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
		tools.Pth.DpdBaseDir, tools.Pth.BjtWordList,
	)
	saveWordList(filePath, WordList)
}
