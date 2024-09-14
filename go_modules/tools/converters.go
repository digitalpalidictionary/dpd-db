package tools

import (
	"fmt"
	"strconv"
)

var pl = fmt.Println

func Str2Rune(s string) []rune {
	return []rune(s)
}

func Int2Str(i int) string {
	return strconv.Itoa(i)
}

func Str2Int(s string) int {
	integer, err := strconv.Atoi(s)
	if err != nil {
		panic(err)
	} else {
		return integer
	}
}

func Float2Str(f float64) string {
	return strconv.FormatFloat(f, 'g', -1, 64)
}
