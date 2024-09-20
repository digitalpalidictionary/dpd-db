package gradient

import "slices"

func MakeGradients(freqList []int, min int, max int) []int {

	s := makeStepsStruct(min, max)
	gradientList := makeGradientList(s, freqList)
	return gradientList
}

func makeGradientList(s stepsStruct, freqList []int) []int {
	gradientList := []int{}
	for _, value := range freqList {

		if value == 0 {
			gradientList = append(gradientList, 0)
		} else if value >= 0 && value < s.s2 {
			gradientList = append(gradientList, 1)
		} else if value >= s.s2 && value < s.s3 {
			gradientList = append(gradientList, 2)
		} else if value >= s.s3 && value < s.s4 {
			gradientList = append(gradientList, 3)
		} else if value >= s.s4 && value < s.s5 {
			gradientList = append(gradientList, 4)
		} else if value >= s.s5 && value < s.s6 {
			gradientList = append(gradientList, 5)
		} else if value >= s.s6 && value < s.s7 {
			gradientList = append(gradientList, 6)
		} else if value >= s.s7 && value < s.s8 {
			gradientList = append(gradientList, 7)
		} else if value >= s.s8 && value < s.s9 {
			gradientList = append(gradientList, 8)
		} else if value >= s.s9 && value < s.s10 {
			gradientList = append(gradientList, 9)
		} else if value == s.s10 {
			gradientList = append(gradientList, 10)
		}
	}
	return gradientList
}

func MinMax(freqList []int) (int, int) {
	max := slices.Max(freqList)
	min := slices.Min(freqList)
	return min, max
}

type stepsStruct struct {
	s0  int
	s1  int
	s2  int
	s3  int
	s4  int
	s5  int
	s6  int
	s7  int
	s8  int
	s9  int
	s10 int
}

func makeStepsStruct(min int, max int) stepsStruct {
	s := stepsStruct{}
	valueRange := max - min
	stepWidth := valueRange / 10
	s.s0 = min
	s.s1 = stepWidth * 1
	s.s2 = stepWidth * 2
	s.s3 = stepWidth * 3
	s.s4 = stepWidth * 4
	s.s5 = stepWidth * 5
	s.s6 = stepWidth * 6
	s.s7 = stepWidth * 7
	s.s8 = stepWidth * 8
	s.s9 = stepWidth * 9
	s.s10 = max
	return s
}
