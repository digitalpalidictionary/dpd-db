package main

import (
	"dpd/go_modules/tools"
	"fmt"
)

var pl = fmt.Println

func main() {
	// x := tools.IniRead("deconstructor", "all_texts")
	pl(tools.IniRead("deconstructor", "all_texts"))
	tools.IniSet("deconstructor", "all_texts", "yes")
	pl(tools.IniRead("deconstructor", "all_texts"))
}
