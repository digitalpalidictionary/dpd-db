package splitters

import (
	"dpd/go_modules/deconstructor/data"
)

func SplitPrefixes(w data.WordData) {

	prefixes := []string{"abhi"}

	for _, prefix := range prefixes {
		if w.StartsWith(prefix) {
			prefixLen := len([]rune(prefix))
			if len(w.Middle) >= prefixLen+2 {
				w.InitNewSplitter()
				data.M.ProcessPlusOne(w)

				w.Front = append(w.Front, prefix)
				w.ToRuleFront(0)
				w.AddWeight(2)
				w.Middle = w.Middle[prefixLen:]
				w.AddPath(prefix)
				w.RecurseFlag = true

				if data.G.IsInInflections(w.Middle) {
					data.M.MakeMatch(prefix, w)
				} else {
					SplitRecursive(w)
				}
				return
			}
		}
	}
}
