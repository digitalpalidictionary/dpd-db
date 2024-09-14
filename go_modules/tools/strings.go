package tools

import "unicode/utf8"

func StrLen(s string) int {
	return utf8.RuneCountInString(s)
}
