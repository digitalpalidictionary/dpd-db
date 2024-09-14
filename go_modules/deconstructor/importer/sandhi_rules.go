package importer

import (
	"gm/deconstructor/data"
	"gm/tools"
	"path/filepath"
)

func makeSandhiRules() []data.SandhiRules {

	filePath := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.SandhiRules,
	)

	dat := tools.ReadTsv(filePath)

	sandhiRulesList := []data.SandhiRules{}

	for count, value := range dat {
		index := tools.Int2Str(count + 2)
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
