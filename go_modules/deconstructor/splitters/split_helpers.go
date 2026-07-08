package splitters

// runeOffsets returns the byte offsets of each rune in s, with a final entry
// equal to len(s). For a string of n runes it has n+1 entries: offsets[k] is the
// byte index where rune k begins, and offsets[n] == len(s). This lets the
// Split2/Split3 hot loops take zero-allocation substrings s[offsets[i]:offsets[j]]
// in place of allocating string([]rune) on every candidate split.
func runeOffsets(s string) []int {
	offsets := make([]int, 0, len(s)+1)
	for i := range s {
		offsets = append(offsets, i)
	}
	offsets = append(offsets, len(s))
	return offsets
}
