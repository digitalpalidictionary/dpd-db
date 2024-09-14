package tools

import (
	"path/filepath"
)

func LoadCstFreqMap() map[string]int {

	cstFreqMap := map[string]int{}
	filePath := filepath.Join(
		Pth.DpdBaseDir,
		Pth.CstFreqMap,
	)
	cstFreqMap = ReadJsonMapStringInt(filePath, cstFreqMap)

	return cstFreqMap
}

func LoadCstBookFreqMap() map[string]map[string]int {

	CstFileFreqMap := map[string]map[string]int{}
	filePath := filepath.Join(
		Pth.DpdBaseDir,
		Pth.CstFileFreqMap,
	)
	CstFileFreqMap = ReadJsonMapStringMapStringInt(filePath, CstFileFreqMap)

	return CstFileFreqMap
}
