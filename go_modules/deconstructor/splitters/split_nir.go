package splitters

import (
	"dpd/go_modules/deconstructor/data"
)

func SplitNir(w data.WordData) {

	if len(w.Middle) > 3 {

		w.InitNewSplitter()
		data.M.ProcessPlusOne(w)
		word := w.Middle
		w.RecurseFlag = true
		processName := "nir"

		w.Front = append(w.Front, "nir")
		w.ToRuleFront(0)
		w.AddWeight(2)

		if word[2] == word[3] {
			// nir followed by double consonant "nis-satta"
			w.Middle = word[3:]
			processName = "nir1"
			w.AddPath(processName)
		} else {
			// nir followed by single vowel "nir-āmisa"
			w.Middle = word[3:]
			processName = "nir2"
			w.AddPath(processName)
		}

		if data.G.IsInInflections(w.Middle) {
			data.M.MakeMatch(processName, w)
		} else {
			SplitRecursive(w)
		}
	}
}
