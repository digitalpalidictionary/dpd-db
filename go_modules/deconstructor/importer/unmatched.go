package importer

import (
	"dpd/go_modules/deconstructor/data"
	"dpd/go_modules/dpdDb"
	"dpd/go_modules/tools"
	"maps"
	"os"
	"path/filepath"
	"strings"
)

type importComponents struct {
	allWords              map[string]string
	cstWords              map[string]string
	bjtWords              map[string]string
	scWords               map[string]string
	syaWords              map[string]string
	dpdWords              map[string]string
	otherPaliWords        map[string]string
	spellingMistakes      map[string]string
	spellingCorrections   map[string]string
	variantVariant        map[string]string
	variantMain           map[string]string
	abbreviations         map[string]string
	manualCorrections     map[string]string
	allInflections        map[string]string
	allInflectionsNoFirst map[string]string
	allInflectionsNoLast  map[string]string
	inflectionExceptions  map[string]string
	unmatched1            map[string]string
	unmatched2            map[string]string
}

var ic = importComponents{
	allWords:              map[string]string{},
	cstWords:              map[string]string{},
	bjtWords:              map[string]string{},
	scWords:               map[string]string{},
	syaWords:              map[string]string{},
	dpdWords:              map[string]string{},
	otherPaliWords:        map[string]string{},
	spellingMistakes:      map[string]string{},
	spellingCorrections:   map[string]string{},
	variantVariant:        map[string]string{},
	variantMain:           map[string]string{},
	abbreviations:         map[string]string{},
	manualCorrections:     map[string]string{},
	allInflections:        map[string]string{},
	allInflectionsNoFirst: map[string]string{},
	allInflectionsNoLast:  map[string]string{},
	inflectionExceptions:  map[string]string{},
	unmatched1:            map[string]string{},
	unmatched2:            map[string]string{},
}

func MakeUnmatched() {

	makeCstWords()
	makeBjtWords()
	makeScWords()
	makeSyaWords()
	makeOtherPaliTexts()
	makeDpdWords()
	makeSpellingMistakes()
	makeVariants()
	makeAbbreviations()
	makeManualCorrections()

	makeInflectionExceptions()
	makeAllInflections()
	makeAllInflectionsNoFirst()
	makeAllInflectionsNoLast()

	ic.allWords = tools.MapUnion(ic.cstWords, ic.scWords)
	ic.allWords = tools.MapUnion(ic.allWords, ic.bjtWords)
	ic.allWords = tools.MapUnion(ic.allWords, ic.syaWords)
	ic.allWords = tools.MapUnion(ic.allWords, ic.otherPaliWords)
	ic.allWords = tools.MapUnion(ic.allWords, ic.dpdWords)
	ic.allWords = tools.MapUnion(ic.allWords, ic.spellingCorrections)
	ic.allWords = tools.MapUnion(ic.allWords, ic.variantMain)

	ic.allWords = tools.MapDifference(ic.allWords, ic.spellingMistakes)
	ic.allWords = tools.MapDifference(ic.allWords, ic.variantVariant)
	ic.allWords = tools.MapDifference(ic.allWords, ic.abbreviations)
	ic.allWords = tools.MapDifference(ic.allWords, ic.manualCorrections)

	ic.unmatched1 = tools.MapDifference(ic.allWords, ic.allInflections)
	ic.unmatched1 = tools.MapDifference(ic.unmatched1, ic.inflectionExceptions)

	if data.L.WordLimit != 0 {
		reduceUnmatched()
	}

	ic.unmatched2 = maps.Clone(ic.unmatched1)
}

func reduceUnmatched() {
	counter := 0
	unmatchedReduced := map[string]string{}
	for word := range ic.unmatched1 {
		if counter >= data.L.WordLimit {
			break
		} else {
			unmatchedReduced[word] = ""
			counter++
		}
	}
	ic.unmatched1 = unmatchedReduced
}

func makeDpdWords() {
	columns := []string{"example_1", "example_2", "commentary"}
	_, results := dpdDb.GetColumns(columns)
	for _, i := range results {

		comp := i.Example1 + " " + i.Example2 + " " + i.Commentary
		compClean := tools.CleanMachine(comp, "ṃ", true, "dpd")
		compCleanList := strings.Fields(compClean)
		for _, word := range compCleanList {
			ic.dpdWords[word] = ""
		}
	}
}

func makeCstWords() {
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.CstWordList,
	)
	CstWordList := []string{}
	CstWordList = tools.ReadJsonSliceString(filePath, CstWordList)
	for _, word := range CstWordList {
		ic.cstWords[word] = ""
	}
}

func makeBjtWords() {
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.BjtWordList,
	)
	BjtWordList := []string{}
	BjtWordList = tools.ReadJsonSliceString(filePath, BjtWordList)
	for _, word := range BjtWordList {
		ic.bjtWords[word] = ""
	}
}

func makeScWords() {
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.ScWordList,
	)
	ScWordList := []string{}
	ScWordList = tools.ReadJsonSliceString(filePath, ScWordList)
	for _, word := range ScWordList {
		ic.scWords[word] = ""
	}
}

func makeSyaWords() {
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.SyaWordList,
	)
	SyaWordList := []string{}
	SyaWordList = tools.ReadJsonSliceString(filePath, SyaWordList)
	for _, word := range SyaWordList {
		ic.syaWords[word] = ""
	}
}

func makeOtherPaliTexts() {
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.OtherPaliTextsDir,
	)
	dir, err := os.ReadDir(filePath)
	tools.HardCheck(err)

	for _, file := range dir {
		fileName := filepath.Join(filePath, file.Name())
		data, err := os.ReadFile(fileName)
		tools.HardCheck(err)

		cleanText := tools.CleanMachine(string(data), "ṃ", true, "other")
		for _, word := range strings.Fields(cleanText) {
			ic.otherPaliWords[word] = ""
		}
	}
}

func makeVariants() {
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.VariantReadings,
	)
	variantMap := tools.ReadTsv(filePath)
	for _, data := range variantMap {
		variant := data["variant"]
		ic.variantVariant[variant] = ""

		main := data["main"]
		ic.variantMain[main] = ""
	}
}

func makeSpellingMistakes() {
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.SpellingMistakes,
	)
	spellingMap := tools.ReadTsv(filePath)
	for _, data := range spellingMap {
		mistake := data["mistake"]
		ic.spellingMistakes[mistake] = ""

		correction := data["correction"]
		ic.spellingCorrections[correction] = ""
	}
}

func makeAbbreviations() {

	db := dpdDb.GetDb()
	columns := []string{"id", "lemma_1", "pos"}
	var results []dpdDb.DpdHeadword
	err := db.Select(columns).
		Where("pos = ?", "abbrev").
		Find(&results)
	tools.HardCheck(err.Error)

	for _, i := range results {
		ic.abbreviations[i.LemmaClean()] = ""
	}
}

func makeManualCorrections() {
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.DeconManualCorrections,
	)

	data := tools.ReadTsv(filePath)
	for _, row := range data {
		word := row["compound"]
		ic.manualCorrections[word] = ""
	}
}

func makeAllInflections() {

	db := dpdDb.GetDb()

	columns := []string{"inflections"}
	exceptionsList := []string{
		"abbrev", "cs", "idiom", "letter", "prefix", "root", "sandhi", "suffix", "ve"}

	var results []dpdDb.DpdHeadword

	err := db.Select(columns).
		Where("pos NOT IN ?", exceptionsList).
		Find(&results)
	tools.HardCheck(err.Error)

	for _, i := range results {
		for _, inflection := range i.InflectionsList() {
			ic.allInflections[inflection] = ""
		}
	}
	delete(ic.allInflections, "")
	ic.allInflections = tools.MapDifference(ic.allInflections, ic.inflectionExceptions)
}

func makeAllInflectionsNoFirst() {
	for word := range ic.allInflections {
		if tools.StrLen(word) > 0 {
			wordR := tools.Str2Rune(word)
			wordR = wordR[1:]
			ic.allInflectionsNoFirst[string(wordR)] = ""
		}
	}
	delete(ic.allInflectionsNoFirst, "")
}

func makeAllInflectionsNoLast() {
	for word := range ic.allInflections {
		if tools.StrLen(word) > 0 {
			wordR := tools.Str2Rune(word)
			wordR = wordR[:len(wordR)-1]
			ic.allInflectionsNoLast[string(wordR)] = ""
		}
	}
	delete(ic.allInflectionsNoLast, "")
}

func makeInflectionExceptions() {
	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.DeconExceptions,
	)
	exceptions := tools.ReadText(filePath)
	for _, word := range exceptions {
		ic.inflectionExceptions[word] = ""
	}
}
