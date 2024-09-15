package tools

import (
	"github.com/fatih/color"
)

var yellow = color.New(color.FgHiYellow)
var green = color.New(color.FgGreen)
var cyan = color.New(color.FgHiCyan)
var red = color.New(color.FgHiRed).Add(color.Bold)
var white = color.New(color.FgWhite)

func PTitle(title string) {
	yellow.Println(title)
}

func PGreenTitle(subtitle string) {
	green.Println(subtitle)
}

func PGreen(subtitle string) {
	green.Printf(subtitle)
}

func PRed(error string) {
	red.Println(error)
}

func PCounter(counter int, total int, word string) {
	if len(word) > 20 {
		word = word[:20]
	}
	cyan.Printf("%10d / %-10d ", counter, total)
	white.Printf("%-20s\n", word)
}
