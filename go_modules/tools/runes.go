package tools

import "strings"

var vowels = "aāiīuūeo"

func IsVowel(letter rune) bool {
	return strings.Contains(vowels, string(letter))
}

func IsConsonant(letter rune) bool {
	return !strings.Contains(vowels, string(letter))
}

func RunesEqual(a, b []rune) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

// Add two slice of runes together
func RunesPlus(a, b []rune) []rune {
	result := make([]rune, len(a)+len(b))
	copy(result, a)
	copy(result[len(a):], b)
	return result
}
