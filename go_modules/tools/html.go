package tools

import "regexp"

// Remove two or more spaces
func CleanWhiteSpace(text string) string {
	r, err := regexp.Compile(` {2,}`)
	Check(err)
	return r.ReplaceAllString(text, "")
}
