package importer

import (
	"dpd/go_modules/deconstructor/data"
	"dpd/go_modules/tools"
	"path/filepath"
)

func makeSandhiRules() []data.SandhiRules {

	filePath := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.SandhiRules,
	)

	dat := tools.ReadTsv(filePath)

	sandhiRulesList := []data.SandhiRules{}

	for _, value := range dat {
		index := tools.Str2Int(value["index"])
		weight := tools.Str2Int(value["weight"])
		sr := data.SandhiRules{
			Index:  index,
			ChA:    tools.Str2Rune(value["chA"]),
			ChB:    tools.Str2Rune(value["chB"]),
			Ch1:    tools.Str2Rune(value["ch1"]),
			Ch2:    tools.Str2Rune(value["ch2"]),
			Eg:     tools.Str2Rune(value["eg"]),
			Weight: weight,
		}
		sandhiRulesList = append(sandhiRulesList, sr)
	}
	return sandhiRulesList

}
