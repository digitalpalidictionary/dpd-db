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

func LoadBjtFreqMap() map[string]int {

	bjtFreqMap := map[string]int{}
	filePath := filepath.Join(
		Pth.DpdBaseDir,
		Pth.BjtFreqMap,
	)
	bjtFreqMap = ReadJsonMapStringInt(filePath, bjtFreqMap)

	return bjtFreqMap
}

func LoadSyaFreqMap() map[string]int {

	syaFreqMap := map[string]int{}
	filePath := filepath.Join(
		Pth.DpdBaseDir,
		Pth.SyaFreqMap,
	)
	syaFreqMap = ReadJsonMapStringInt(filePath, syaFreqMap)

	return syaFreqMap
}

func LoadScFreqMap() map[string]int {

	scFreqMap := map[string]int{}
	filePath := filepath.Join(
		Pth.DpdBaseDir,
		Pth.ScFreqMap,
	)
	scFreqMap = ReadJsonMapStringInt(filePath, scFreqMap)

	return scFreqMap
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
