package tools

func HardCheck(e error) {
	if e != nil {
		panic(e)
	}
}
