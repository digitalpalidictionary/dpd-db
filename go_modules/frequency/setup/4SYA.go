package main

import (
	"dpd/go_modules/tools"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// The Syāmaraṭṭha edition packs Vimānavatthu, Petavatthu, Theragāthā and
// Therīgāthā into one physical volume. Th/Thi belong in Khuddaka 1 but Vv/Pv
// in Khuddaka 2, so the whole-file mapping mis-buckets Th/Thi. syaFileSlices
// splits this one volume at the (unique) Theragāthā heading so each half maps
// to its correct bucket in sya_file_map.json. The two synthetic keys are also
// referenced by scripts/build/ebt_counter.py.
const (
	syaCombinedVol = "Canonical/26-Vv-Pv-Th-Thi.txt"
	syaTheraMarker = "suttantapiṭake khuddakanikāyassa theragāthā"
	syaVvPvKey     = "Canonical/26-Vv-Pv-Th-Thi.txt::vv-pv"
	syaThThiKey    = "Canonical/26-Vv-Pv-Th-Thi.txt::th-thi"
)

// syaFileSlices returns the frequency-map key(s) and raw text for one SYA
// source file: a single slice keyed by its own path, except the combined
// volume 26, split at the Theragāthā heading (that line and everything after
// it is Th+Thi; everything before is Vv+Pv). Splitting on the whole-line
// heading preserves the exact word multiset.
func syaFileSlices(relKey string, text string) map[string]string {
	if relKey != syaCombinedVol {
		return map[string]string{relKey: text}
	}
	idx := strings.Index(text, syaTheraMarker)
	if idx == -1 {
		tools.HardCheck(fmt.Errorf("theragāthā marker not found in %s", relKey))
	}
	return map[string]string{
		syaVvPvKey:  text[:idx],
		syaThThiKey: text[idx:],
	}
}

func makeSyaFreq() {
	tools.PGreenTitle("Save word frequency in Thai texts to JSON")

	fileFreqMap := map[string]map[string]int{}

	baseDir := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.SyaTextDir,
	)

	folders := []string{"Canonical", "Non-Canonical"}

	counter := 1
	for _, folder := range folders {
		dirName := filepath.Join(baseDir, folder)

		directory, err := os.ReadDir(dirName)
		tools.HardCheck(err)

		for _, file := range directory {
			if file.Name() == ".DS_Store" {
				continue
			}

			fileName := file.Name()
			filePath := filepath.Join(dirName, fileName)
			filePathRel, err := filepath.Rel(baseDir, filePath)
			tools.HardCheck(err)
			tools.PCounter(counter, 115, filePath)

			dataRead, err := os.ReadFile(filePath)
			tools.HardCheck(err)

			text := strings.TrimPrefix(string(dataRead), "\uFEFF")
			for key, sliceText := range syaFileSlices(filePathRel, text) {
				textClean := tools.CleanMachine(sliceText, "ṃ", false, "sya")
				textList := strings.Fields(textClean)
				fileFreqMap[key] = tools.ListCounter(textList)
			}
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
