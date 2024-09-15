package tools

import (
	"fmt"
	"time"

	"github.com/fatih/color"
)

type TicToc struct {
	startTime time.Time
}

func Tic() TicToc {
	t := TicToc{}
	t.startTime = time.Now()
	return t
}

func (t TicToc) Toc() {
	cyan := color.New(color.FgCyan)
	cyan.Println("----------------------------------------")
	cyan.Printf("%v\n\n", t.formatTime())
}

func (t TicToc) formatTime() string {
	duration := time.Since(t.startTime)
	seconds := int(duration.Seconds()) % 60
	minutes := int(duration.Minutes()) % 60
	hours := int(duration.Hours())
	return fmt.Sprintf("%d:%02d:%02d.%06d", hours, minutes, seconds, duration.Microseconds()%1000000)
}
