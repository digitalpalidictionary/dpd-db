package splitters

import (
	"gm/deconstructor/data"
)

func SplitDoubleLetter(w data.WordData) {

	w.InitNewSplitter("remove-double")
	data.M.ProcessPlusOne(w)
	w.RecurseFlag = true
	processName := "remove-double"

	w.Middle = w.Middle[1:]

	if data.G.IsInInflections(w.Middle) {
		w.ToRuleFront("0")
		w.AddWeight(1)
		data.M.MakeMatch(processName, w)
	} else {
		w.ToRuleFront("0")
		w.AddWeight(2)
		SplitRecursive(w)
	}
}
