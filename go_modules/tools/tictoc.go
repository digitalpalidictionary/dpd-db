package tools

import "time"

type TicToc struct {
	startTime time.Time
}

func Tic() TicToc {
	t := TicToc{}
	t.startTime = time.Now()
	return t
}

func (t TicToc) Toc(text string) {
	pf("%v%v\n", text, time.Since(t.startTime))
}
