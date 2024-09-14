package tools

// Return a map with the frequency of each string in a list.
func ListCounter(list []string) map[string]int {
	counter := map[string]int{}
	for _, word := range list {
		// count, exists := counter[word]
		counter[word]++
	}
	return counter
}
