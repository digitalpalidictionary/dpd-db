package tools

import "slices"

var Indeclinables = []string{
	"abbrev",
	"abs",
	"ger",
	"idiom",
	"ind",
	"inf",
	"prefix",
	"suffix",
	"var",
	"sandhi",
}

var Conjugations = []string{
	"aor",
	"cond",
	"fut",
	"imp",
	"imperf",
	"opt",
	"perf",
	"pr",
}

var Declensions = []string{
	"adj",
	"card",
	"cs",
	"fem",
	"letter",
	"masc",
	"nt",
	"ordin",
	"pp",
	"pron",
	"prp",
	"ptp",
	"root",
	"ve",
}

func TestPosType(pos string) string {
	if slices.Contains(Indeclinables, pos) {
		return "indeclinable"
	} else if slices.Contains(Conjugations, pos) {
		return "conjugation"
	} else if slices.Contains(Declensions, pos) {
		return "declension"
	} else {
		return ""
	}
}
