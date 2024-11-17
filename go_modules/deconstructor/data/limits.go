package data

var L = InitLimits()

type Limits struct {
	Recursive          bool
	WordLimit          int
	CountEvery         int
	MaxWordLength      int
	MaxProcessesSingle int
	MaxProcessesTotal  int
	LwCleanListMaxLen  int
	LwCleanMinLen      int
	LwFuzzyListMaxLen  int
	LwFuzzyMinLen      int
	TopDictLimit       int
}

func InitLimits() Limits {
	var l = Limits{}           // defaults
	l.Recursive = true         // true
	l.WordLimit = 0            // 0
	l.CountEvery = 25000       // 10000 - 50000
	l.MaxWordLength = 0        // 0
	l.MaxProcessesSingle = 20  // 15-20
	l.MaxProcessesTotal = 2000 // 1000-2000
	l.LwCleanListMaxLen = 5    // 5
	l.LwCleanMinLen = 4        // 4
	l.LwFuzzyListMaxLen = 5    // 5
	l.LwFuzzyMinLen = 3        // 3
	l.TopDictLimit = 5         // 5 entries in GoldenDict
	return l
}
