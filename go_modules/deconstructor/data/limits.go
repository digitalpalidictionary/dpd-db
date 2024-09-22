package data

var L = InitLimits()

type Limits struct {
	Recursive          bool
	IgnoreTried        bool
	UnMatchedLimit     int
	Counter            int
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
	l.IgnoreTried = false      // false
	l.UnMatchedLimit = 100     // 0
	l.Counter = 25000          // 10000
	l.MaxWordLength = 0        // 0
	l.MaxProcessesSingle = 15  // 15-20
	l.MaxProcessesTotal = 1500 // 1000-2000
	l.LwCleanListMaxLen = 4    // 5
	l.LwCleanMinLen = 3        // 4
	l.LwFuzzyListMaxLen = 5    // 5
	l.LwFuzzyMinLen = 2        // 4
	l.TopDictLimit = 5         // 5 entries in GoldenDict
	return l
}
