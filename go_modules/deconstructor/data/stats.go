package data

import (
	"cmp"
	"dpd/go_modules/tools"
	"os"
	"slices"
	"time"
)

type statistics struct {
	word      string
	time      float64
	matched   string
	processes string
	comment   string
}

func (m *MatchData) SaveWordStats(w WordData) {
	s := statistics{}
	s.word = string(w.Word)
	s.time = float64(time.Since(w.StartTime).Seconds())

	Mu.Lock()
	_, exists := m.MatchedMap[string(w.Word)]
	Mu.Unlock()
	s.matched = spf("%v", exists)

	s.processes = tools.Int2Str(m.ProcessCounter(w))
	s.comment = ""
	Mu.Lock()
	m.WordStats = append(m.WordStats, s)
	Mu.Unlock()
}

func (m MatchData) SaveStatsTsv() {
	pf("saving stats:		")
	filePath := tools.Pth.StatsTsv
	header := []string{
		"word", "time", "matched", "processes", "comment",
	}

	slices.SortFunc(m.WordStats, func(a, b statistics) int {
		return cmp.Compare(b.time, a.time)
	})

	statsData := [][]string{}
	for _, s := range m.WordStats {
		dataRow := []string{
			s.word, tools.Float2Str(s.time), s.matched, s.processes, s.comment,
		}
		statsData = append(statsData, dataRow)
	}
	tools.SaveTsv(filePath, "\t", header, statsData)
	fileInfo, _ := os.Stat(filePath)
	pf("%v rows, %.1fMB\n", len(statsData), float64(fileInfo.Size())/1000/1000)
}
