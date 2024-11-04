package splitters

import (
	"dpd/go_modules/deconstructor/data"
	"strings"
)

func SplitRecursive(w data.WordData) {

	if data.M.NotTriedYet(w) {
		if (data.L.MaxProcessesSingle == 0 ||
			w.ProcessCount <= data.L.MaxProcessesSingle) &&
			(data.L.MaxProcessesTotal == 0 ||
				data.M.ProcessCounter(w) <= data.L.MaxProcessesTotal) {

			if data.M.HasNoMatches(w) || w.LwffLwfbFlag {
				SplitLwff(w)
			}
			if data.M.HasNoMatches(w) || w.LwffLwfbFlag {
				SplitLwfb(w)
			}

			if w.ProcessCount < 1 {
				if w.StartsWith("ati") {
					SplitAti(w)
				} else if w.StartsWith("nāti") {
					SplitAti(w)
				} else if w.HasNegPrefix() {
					SplitNeg(w)
				} else if w.StartsWith("sa") {
					SplitSa(w)
				} else if w.StartsWith("su") {
					SplitSu(w)
				} else if w.StartsWith("du") {
					SplitDur(w)
				} else if w.EndsWithList([]string{"tissa", "tissā"}) {
					SplitTissa(w)
				} else if w.EndsWithList([]string{"pi", "ca", "va", "ti"}) {
					SplitApiCaEvaIti(w)
				}
			}
			if w.EndsWith("ādi") {
				SplitAdi(w)
			}
			if w.EndsWith("pīti") {
				SplitPiti(w)
			}
			if w.HasInitialDouble() {
				SplitDoubleLetter(w)
			}
			// split fem and nt abstract suffixes
			if w.EndsWithList([]string{"tā", "tta", "ttā", "tāya", "tāyaṃ"}) {
				SplitTta(w)
			}
			if w.ProcessCount >= 1 {
				Split2(w)
				Split3(w)
			}

		} else {
			data.MaxedOut++
		}
	} else {
		data.BlockedTries++
	}
}

func Debugger(w data.WordData) {
	if !strings.HasSuffix(w.MakeSplitString(), "paṃ") {
		w.PrintSplitString()
	}
}
