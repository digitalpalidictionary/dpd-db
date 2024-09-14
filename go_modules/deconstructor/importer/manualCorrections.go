package importer

import (
	"gm/deconstructor/data"
	"gm/tools"
	"path/filepath"
)

// Add manual deconstructions to a list of MatchItems.
// It's the start of the list of matches.
func makeMatchItems() []data.MatchItem {

	filePath := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.DeconManualCorrections,
	)

	dat := tools.ReadTsv(filePath)

	manualDecon := []data.MatchItem{}

	for _, d := range dat {
		mi := data.MatchItem{}
		mi.Word = d["compound"]
		mi.Split = d["split"]
		mi.SplitCount = 0
		mi.SplitRatio = 0
		mi.Route = ""
		mi.FinalProcess = ""
		mi.Rules = "manual"
		mi.Weight = 0
		mi.FinalProcess = ""
		mi.ProcessCount = 0
		mi.Time = 0

		manualDecon = append(manualDecon, mi)
	}
	return manualDecon
}
