package tools

import (
	"fmt"

	"github.com/fatih/color"
)

var yellow = color.New(color.FgHiYellow)
var green = color.New(color.FgGreen)
var cyan = color.New(color.FgHiCyan)
var red = color.New(color.FgHiRed).Add(color.Bold)
var white = color.New(color.FgWhite)

func PTitle(title string) {
	fmt.Println()
	yellow.Println(title)
}

func PGreenTitle(subtitle string) {
	green.Println(subtitle)
}

func PGreen(subtitle string) {
	green.Printf("%-30s", subtitle)
}

func PRed(error string) {
	red.Println(error)
}

func POk(text any) {
	white.Println(text)
}

func PCounter(counter int, total int, word string) {
	cyan.Printf("%10d / %-10d ", counter, total)
	white.Printf("%-20s\n", word)
}
