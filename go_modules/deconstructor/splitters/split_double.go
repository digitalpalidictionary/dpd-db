package splitters

import (
	"dpd/go_modules/deconstructor/data"
)

func SplitDoubleLetter(w data.WordData) {

	w.InitNewSplitter()
	data.M.ProcessPlusOne(w)
	w.RecurseFlag = true
	processName := "-double"

	w.Middle = w.Middle[1:]

	if data.G.IsInInflections(w.Middle) {
		w.ToRuleFront(0)
		w.AddWeight(1)
		w.AddPath(processName)
		data.M.MakeMatch(processName, w)
	} else {
		w.ToRuleFront(0)
		w.AddWeight(2)
		w.AddPath(processName)
		SplitRecursive(w)
	}
}
