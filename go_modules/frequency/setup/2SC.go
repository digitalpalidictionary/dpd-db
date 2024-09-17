package main

import (
	"dpd/go_modules/tools"
	"io/fs"
	"os"
	"path/filepath"
	"slices"
	"strings"
)

func makeScFreq() {
	tools.PGreenTitle("Save word frequency in Sutta Central to JSON")

	fileFreqMap := map[string]map[string]int{}

	baseDir := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.ScJsonTextDir,
	)

	fileList := makeFileList(baseDir)
	// writeFileList(fileList) // such a mad filesystem!

	for i, fileName := range fileList {
		filePath := filepath.Join(baseDir, fileName)
		relPath, err := filepath.Rel(baseDir, filePath)
		tools.HardCheck(err)
		tools.PCounter(i+1, len(fileList), relPath)

		var jsonData map[string]string
		jsonData = tools.ReadJsonMapStringString(filePath, jsonData)

		compiledText := ""
		for _, text := range jsonData {
			compiledText = compiledText + text
		}

		textClean := tools.CleanMachine(compiledText, "ṃ", true, "sc")
		textList := strings.Fields(textClean)
		freqMap := tools.ListCounter(textList)
		fileFreqMap[fileName] = freqMap
	}

	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.ScFileFreqMap,
	)

	saveFileFreqMap(filePath, fileFreqMap)

	freqMap := makeFreqMap(fileFreqMap)

	filePath = filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.ScFreqMap,
	)

	saveFreqMap(filePath, freqMap)

	WordList := makeWordList(freqMap)

	filePath = filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.ScWordList,
	)

	saveWordList(filePath, WordList)

}

func makeFileList(baseDir string) []string {
	fileList := []string{}
	skipFolder := "xplayground"

	err := filepath.Walk(
		baseDir,
		func(path string, info fs.FileInfo, err error) error {
			tools.HardCheck(err)

			if info.IsDir() && info.Name() == skipFolder {
				return filepath.SkipDir
			}
			if !info.IsDir() {
				relativePath, err := filepath.Rel(baseDir, path)
				tools.HardCheck(err)
				fileList = append(fileList, relativePath)
			}
			return nil
		})
	tools.HardCheck(err)
	return fileList
}

func writeFileList(fileList []string) {
	fileString := ""
	slices.Sort(fileList)
	for _, file := range fileList {
		fileString = fileString + file + "\n"
	}
	file, err := os.Create("temp.txt")
	tools.HardCheck(err)
	file.Write([]byte(fileString))
}
