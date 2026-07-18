package main

import (
	"dpd/go_modules/tools"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"unicode"
)

func makeScFreq() {
	tools.PGreenTitle("Save word frequency in Sutta Central to JSON")

	fileFreqMap := map[string]map[string]int{}

	baseDir := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.ScJsonTextDir,
	)

	fileList := makeFileList(baseDir)

	for i, fileName := range fileList {
		filePath := filepath.Join(baseDir, fileName)
		relPath, err := filepath.Rel(baseDir, filePath)
		tools.HardCheck(err)
		tools.PCounter(i+1, len(fileList), relPath)

		var jsonData map[string]string
		jsonData = tools.ReadJsonMapStringString(filePath, jsonData)

		compiledText := ""
		for _, text := range jsonData {
			compiledText = compiledText + text
		}

		compiledText = compiledText + " " + scVariantText(fileName)

		textClean := tools.CleanMachine(compiledText, "ṃ", true, "sc")
		textList := strings.Fields(textClean)
		freqMap := tools.ListCounter(textList)
		fileFreqMap[fileName] = freqMap
	}

	filePath := filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.ScFileFreqMap,
	)

	saveFileFreqMap(filePath, fileFreqMap)

	freqMap := makeFreqMap(fileFreqMap)

	filePath = filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.ScFreqMap,
	)

	saveFreqMap(filePath, freqMap)

	WordList := makeWordList(freqMap)

	filePath = filepath.Join(
		tools.Pth.DpdBaseDir, tools.Pth.ScWordList,
	)

	saveWordList(filePath, WordList)

}

var witnessRe = regexp.MustCompile(`\([^)]*\)`)

// a witness code outside parens means the clause is an editorial note
// ("idaṁ padaṁ cck, pts-vp-pli1 potthakesu…"), not a variant reading
var noteRe = regexp.MustCompile(
	`(^|[\s,.])(bj|cck|km|mr|si|s1-3|sya-all|sya\ded|pts\d(ed)?|pts-vp-pli\d?|csp\ded|potthakesu|etthantare)([\s,.]|$)`,
)

// digits, colons and brackets only occur in citation references
// ("dn33:194 [Saṅgītisutta]"), never in variant readings
var citeCharRe = regexp.MustCompile(`[0-9:\[\]]`)

// scVariantText returns the variant readings belonging to a root file,
// or "" if the file has no variant twin.
func scVariantText(rootRelPath string) string {
	variantRelPath := strings.Replace(
		rootRelPath, "_root-pli-ms.json", "_variant-pli-ms.json", 1,
	)
	variantPath := filepath.Join(
		tools.Pth.DpdBaseDir,
		tools.Pth.ScVariantTextDir,
		variantRelPath,
	)
	if _, err := os.Stat(variantPath); err != nil {
		if !os.IsNotExist(err) {
			tools.HardCheck(err)
		}
		return ""
	}

	var jsonData map[string]string
	jsonData = tools.ReadJsonMapStringString(variantPath, jsonData)

	variantText := ""
	for _, entry := range jsonData {
		variantText = variantText + " " + extractVariantWords(entry)
	}
	return variantText
}

// extractVariantWords pulls only the variant readings from one entry like
// "mudiṅgasaddo → mutiṅgasaddo (bj) | lambikaṁ → lapilakaṁ (bj); lampikaṁ (si)".
// Mūla words left of "→" are skipped (already counted from the root text) and
// witness abbreviations in parentheses are stripped. A clause without "→" is a
// continuation whose whole text is the variant reading.
func extractVariantWords(entry string) string {
	words := []string{}
	for _, clause := range strings.Split(entry, "|") {
		if _, rhs, found := strings.Cut(clause, "→"); found {
			clause = rhs
		}
		clause = witnessRe.ReplaceAllString(clause, " ")
		// an unclosed "(" starts an unterminated witness/citation group:
		// everything from it onwards is junk, not variant text
		if i := strings.Index(clause, "("); i >= 0 {
			clause = clause[:i]
		}
		if noteRe.MatchString(clause) {
			continue
		}
		// "/" is a verse line separator in readings and a path separator
		// in citations — a space is correct for both; "'" is sandhi
		// elision and joins its parts, as in CleanMachine's cst branch
		clause = strings.NewReplacer(
			"→", " ", ")", " ", "/", " ", "'", "",
		).Replace(clause)
		for _, word := range strings.Fields(clause) {
			if citeCharRe.MatchString(word) {
				continue
			}
			if !strings.ContainsFunc(word, unicode.IsLetter) {
				continue
			}
			words = append(words, word)
		}
	}
	return strings.Join(words, " ")
}

func makeFileList(baseDir string) []string {
	fileList := []string{}
	skipFolder := "xplayground"

	err := filepath.Walk(
		baseDir,
		func(path string, info fs.FileInfo, err error) error {
			tools.HardCheck(err)

			if info.IsDir() && info.Name() == skipFolder {
				return filepath.SkipDir
			}
			if !info.IsDir() && info.Name() != ".DS_Store" {
				relativePath, err := filepath.Rel(baseDir, path)
				tools.HardCheck(err)
				fileList = append(fileList, relativePath)
			}
			return nil
		})
	tools.HardCheck(err)
	return fileList
}
