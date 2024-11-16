package importer

import (
	"dpd/go_modules/deconstructor/data"
	"dpd/go_modules/tools"
	"path/filepath"
	"strings"
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
		mi.Split = strings.TrimSpace(d["split"])
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
