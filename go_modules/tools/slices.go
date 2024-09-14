package tools

func IsAllZero(intSlice []int) bool {
	for _, num := range intSlice {
		if num != 0 {
			return false
		}
	}
	return true
}
