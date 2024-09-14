package tools

import "fmt"

func Pause() {
	fmt.Printf("press any key to continue... ")
	fmt.Scanln()
}
