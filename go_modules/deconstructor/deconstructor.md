# Why?

# How?

# Short Variables:
```go
var g 	GlobalData
var m 	MatchData
var w 	WordData
var wg	WaitGroup
var mu  RMMutex
var pl 	fmt.Println
var pf 	fmt.Printf
var spf fmt.SPrintf
```

# TODO Next
- make []failedItem
- split match processing into own function
- index rules explicitly

# TODO
- with all recursive functions, don't take a step beyond what you need to, eliminate possibilities upfront with noLastLetter and noFirstLetter checks
- compare results with original
- what parts of original deconstructor need to be integrated?
- Why are there dupes in non-matches?
- Are there dupes in matches too?

# TODO Maybe
- List of all successful and failed attempts for heavier processes, just return those results
- total recursion count