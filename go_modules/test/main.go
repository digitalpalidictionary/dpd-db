package main

import (
	"dpd/go_modules/tools"
	"fmt"
)

var pl = fmt.Println

func main() {
	t := tools.Tic()
	tools.PTitle("this is the program")
	tools.PGreenTitle("is does some stuff")

	i := 10
	for count := range i {
		tools.PCounter(count, i, "some text")
	}

	tools.PGreenTitle("and then it finsihes")

	t.Toc()
}
