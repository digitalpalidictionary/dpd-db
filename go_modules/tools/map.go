package tools

func MapUnion[C comparable, A any](mapA, mapB map[C]A) map[C]A {
	union := map[C]A{}
	for key, value := range mapA {
		union[key] = value
	}
	for key, value := range mapB {
		union[key] = value
	}
	return union
}

// All values in A not contained in B
func MapDoesNotContain[C comparable](mapA, mapB map[C]string) map[C]string {
	difference := make(map[C]string)
	for key := range mapA {
		_, exists := mapB[key]
		if exists {
			difference[key] = ""
		}
	}
	return difference
}

// Remove any value from A which is found in B
func MapDifference[C comparable](mapA, mapB map[C]string) map[C]string {
	difference := make(map[C]string)
	for key := range mapA {
		_, exists := mapB[key]
		if !exists {
			difference[key] = ""
		}
	}
	return difference
}

// if value in mapb exists in mapa, then remove it from mapa
