package tools

func RangeTsv(daSlice []map[string]string) {
	for i, daMap := range daSlice {
		pl(i, daMap)
	}
}

func RangeMap(daMap map[string]string) {
	for key, value := range daMap {
		pl(key, value)
	}
}

func RangeSlice[T any](daSlice []T) {
	for i, value := range daSlice {
		pl(i, value)
	}
}
