package gradient

import "slices"

func MinMax(freqList []int) (int, int) {
	max := slices.Max(freqList)
	min := slices.Min(freqList)
	return min, max
}

// MakeGradients buckets each frequency into a heatmap level 0-10.
//
// Bucket thresholds are multiples of stepWidth = (max-min)/10 — note
// they are NOT offset by min, a pre-existing quirk kept as-is (see
// kamma thread 20260707_frequency_go_study; changing it is a separate
// decision).
func MakeGradients(freqList []int, min int, max int) []int {
	stepWidth := (max - min) / 10

	gradientList := make([]int, len(freqList))
	for i, value := range freqList {
		gradientList[i] = bucket(value, stepWidth, max)
	}
	return gradientList
}

// bucket finds the largest level L in [2,9] with value >= stepWidth*L,
// falling back to 1, except for the value==0 and value==max edges.
func bucket(value int, stepWidth int, max int) int {
	if value == 0 {
		return 0
	}
	if value == max {
		return 10
	}
	for level := 9; level >= 2; level-- {
		if value >= stepWidth*level {
			return level
		}
	}
	return 1
}
