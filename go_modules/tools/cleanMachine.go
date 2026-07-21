package tools

import (
	"fmt"
	"regexp"
	"strings"
)

var pf = fmt.Printf

// A text cleaning machine.
//
//   - Returns clean text with only allowable characters.
//   - Change the niggahita character to "ṃ", "ṁ" or "ŋ"
//   - Optionally add all parts of hyphenated words
//   - source options are "cst", "sc", "bjt", "sya", "dpd", "other" (This controls which characters are allowable).
func CleanMachine(text string, niggahita string, addHyphenatedWords bool, source string) string {

	// lower case
	text = strings.ToLower(text)

	// remove digits
	r, err := regexp.Compile(`\d`)
	HardCheck(err)
	text = r.ReplaceAllString(text, " ")

	// remove tabs
	r, err = regexp.Compile(`\t`)
	HardCheck(err)
	text = r.ReplaceAllString(text, " ")

	// remove new lines
	r, err = regexp.Compile(`\n`)
	HardCheck(err)
	text = r.ReplaceAllString(text, " ")

	// standardize niggahitas
	if niggahita == "ṃ" {
		text = strings.Replace(text, "ṁ", "ṃ", -1)
		text = strings.Replace(text, "ŋ", "ṃ", -1)
	} else if niggahita == "ṁ" {
		text = strings.Replace(text, "ṃ", "ṁ", -1)
		text = strings.Replace(text, "ŋ", "ṁ", -1)
	} else if niggahita == "ŋ" {
		text = strings.Replace(text, "ṃ", "ŋ", -1)
		text = strings.Replace(text, "ṁ", "ŋ", -1)
	}

	switch source {

	case "cst":
		// replace letters
		text = strings.Replace(text, `t_`, `v`, -1) // ???
		text = strings.Replace(text, `ï`, `i`, -1)
		text = strings.Replace(text, `ü`, `u`, -1)

		// no space
		text = strings.Replace(text, `'`, ``, -1)
		text = strings.Replace(text, "`", ``, -1)
		text = strings.Replace(text, "_", ``, -1)

		// needs space
		text = strings.Replace(text, `+`, ` `, -1)
		text = strings.Replace(text, `=`, ` `, -1)
		text = strings.Replace(text, `^`, ` `, -1)
		text = strings.Replace(text, `\`, ` `, -1)
		text = strings.Replace(text, `§`, ` `, -1)
		text = strings.Replace(text, ` - `, ` `, -1)
		text = strings.Replace(text, `॰`, ` `, -1)
		text = strings.Replace(text, `ḥ`, ` `, -1)
		text = strings.Replace(text, `ṛ`, ` `, -1)

	case "sc":
		text = strings.Replace(text, `<b>`, ` `, -1)
		text = strings.Replace(text, `</b>`, ` `, -1)

		text = strings.Replace(text, `“`, ``, -1)
		text = strings.Replace(text, `”`, ``, -1)
		text = strings.Replace(text, `ạ`, `a`, -1)
		text = strings.Replace(text, `~`, ``, -1)

	case "bjt":
		// letters
		text = strings.Replace(text, `n̆`, `ṅ`, -1)
		text = strings.Replace(text, `ṉ`, `n`, -1)
		text = strings.Replace(text, `ṟ`, `r`, -1)
		text = strings.Replace(text, `ġ`, `g`, -1)
		text = strings.Replace(text, `ẏ`, `g`, -1)
		text = strings.Replace(text, `k͟`, `k`, -1)
		text = strings.Replace(text, `ǣ`, `ā`, -1) // tell janaka
		text = strings.Replace(text, `ś`, `s`, -1) // tell janaka
		text = strings.Replace(text, `ṛ`, `ā`, -1) // tell janaka
		text = strings.Replace(text, `æ`, `u`, -1) // tell janaka
		text = strings.Replace(text, `z`, `j`, -1) // tell janaka
		text = strings.Replace(text, `q`, `k`, -1) // tell janaka

		text = strings.Replace(text, `f`, ``, -1) // tell janaka
		text = strings.Replace(text, `x`, ``, -1) // tell janaka
		text = strings.Replace(text, `l̤`, ``, -1)

		// no space
		text = strings.Replace(text, `”`, ``, -1)
		text = strings.Replace(text, `“`, ``, -1)
		text = strings.Replace(text, `'`, ``, -1)
		text = strings.Replace(text, `†`, ``, -1)
		text = strings.Replace(text, `_`, ``, -1)
		text = strings.Replace(text, `$`, ``, -1)
		text = strings.Replace(text, `<hr/>`, ``, -1)
		text = strings.Replace(text, `^`, ``, -1)
		text = strings.Replace(text, `\`, ``, -1)
		text = strings.Replace(text, `‡`, ``, -1)
		text = strings.Replace(text, `*`, ``, -1)

		// needs space

		text = strings.Replace(text, `=`, ` `, -1)
		text = strings.Replace(text, `>`, ` `, -1)
		text = strings.Replace(text, `+`, ` `, -1)
		text = strings.Replace(text, `/`, ` `, -1)

		text = strings.Replace(text, string(rune('\u0308')), ` `, -1) // ̈
		text = strings.Replace(text, string(rune('\u00A0')), ` `, -1) // NO BREAK SPACE

	case "sya":

		// remove pts ref and html markup
		r := regexp.MustCompile(`<.+?>`)
		text = r.ReplaceAllString(text, " ")

		// remove structural markers of the corrected BUDSIR corpus so their
		// literal words do not pollute the frequency map (digits already stripped)
		r = regexp.MustCompile(`\(pts[^)]*\)`)
		text = r.ReplaceAllString(text, " ")
		text = strings.Replace(text, "page number", " ", -1)
		text = strings.Replace(text, "footnote", " ", -1)

		// remove words with crazy characters

		fstring := fmt.Sprintf(`\S*(%v|%v|%v|%v|%v)\S*`,
			string(rune(35303)), // 觧
			string(rune(35053)), // 裭
			string(rune(37114)), // 郺
			string(rune(37267)), // 醓
			string(rune(1912)),  // ݸ
		)
		r, err = regexp.Compile(fstring)
		HardCheck(err)
		text = r.ReplaceAllString(text, " ")

		// replace letter
		text = strings.Replace(text, `ḥ`, `h`, -1)
		text = strings.Replace(text, `@`, `ā`, -1)

		// keep space
		text = strings.Replace(text, `*`, ` `, -1)
		text = strings.Replace(text, `/`, ` `, -1)
		text = strings.Replace(text, `#`, ` `, -1)
		text = strings.Replace(text, `=`, ` `, -1)
		text = strings.Replace(text, `$`, ` `, -1)

		// no space
		text = strings.Replace(text, `"`, ``, -1)
		text = strings.Replace(text, "`", ``, -1)
		text = strings.Replace(text, `'`, ``, -1)

		text = strings.Replace(text, string(rune(13)), ` `, -1) // \r

	case "dpd":

		// remove <b> tags
		r, err = regexp.Compile(`<b>|</b>`)
		HardCheck(err)
		text = r.ReplaceAllString(text, "")

		text = strings.Replace(text, `'`, ``, -1)
		text = strings.Replace(text, `+`, ``, -1)
		text = strings.Replace(text, `=`, ``, -1)

	case "other":
		// no space
		text = strings.Replace(text, `“`, ``, -1)
		text = strings.Replace(text, `”`, ``, -1)
		text = strings.Replace(text, `"`, ``, -1)
		text = strings.Replace(text, `'`, ``, -1)
		text = strings.Replace(text, `*`, ``, -1)
		text = strings.Replace(text, `text`, ``, -1)
		text = strings.Replace(text, string(rune('\u00AD')), ``, -1) // SOFT HYPHEN

		// space
		text = strings.Replace(text, string(rune('\u000D')), ` `, -1) // CARRIAGE RETURN
		text = strings.Replace(text, string(rune('\u00A0')), ` `, -1) // NO-BREAK SPACE

	}

	// common
	text = strings.Replace(text, `.`, ` `, -1)
	text = strings.Replace(text, `,`, ` `, -1)
	text = strings.Replace(text, `;`, ` `, -1)
	text = strings.Replace(text, `:`, ` `, -1)

	text = strings.Replace(text, `?`, ``, -1)
	text = strings.Replace(text, `!`, ``, -1)

	text = strings.Replace(text, `‘`, ``, -1)
	text = strings.Replace(text, `’`, ``, -1)

	text = strings.Replace(text, `(`, ` `, -1)
	text = strings.Replace(text, `)`, ` `, -1)
	text = strings.Replace(text, `[`, ` `, -1)
	text = strings.Replace(text, `]`, ` `, -1)
	text = strings.Replace(text, `{`, ` `, -1)
	text = strings.Replace(text, `}`, ` `, -1)

	text = strings.Replace(text, `–`, ` `, -1)
	text = strings.Replace(text, `—`, ` `, -1)
	text = strings.Replace(text, `…`, ` `, -1)

	// deal with hyphens
	if addHyphenatedWords {
		r, err = regexp.Compile(`.[^ ]*?-.*? `)
		HardCheck(err)
		hyphenatedList := r.FindAllString(text, -1)

		text = strings.Replace(text, `-`, ``, -1)

		hyphenatedWords := ""
		for _, h := range hyphenatedList {
			h = strings.Replace(h, `-`, ` `, -1)
			hyphenatedWords = " " + hyphenatedWords + " " + h
		}
		text = text + " " + hyphenatedWords + " "
	} else {
		text = strings.Replace(text, `-`, ``, -1)
	}

	// remove extra spaces
	r, err = regexp.Compile(` +`)
	HardCheck(err)
	text = r.ReplaceAllString(text, " ")

	// check error
	characterTest(text, source)

	return text

}

// Test for allowable characters and report errors.
//
//	textSet options are "cst", "sc", "bjt"
func characterTest(text string, textSet string) {
	allowedCharacters := "aāiīuūeokgṅcjñṭḍṇtdnpbmyrlsvhḷṃṁ\n "
	bjtExtraChar := "ṣḥ" // xfśǣæwqṛz
	scExtraChar := "fw"
	syaExtraChar := "f"
	otherExtraChar := "fxqw"

	switch textSet {
	case "bjt":
		allowedCharacters = allowedCharacters + bjtExtraChar
	case "sc":
		allowedCharacters = allowedCharacters + scExtraChar
	case "sya":
		allowedCharacters = allowedCharacters + syaExtraChar
	case "other":
		allowedCharacters = allowedCharacters + otherExtraChar
	}

	errors := []rune{}
	for _, ch := range text {
		if !strings.Contains(allowedCharacters, string(ch)) {
			errors = append(errors, ch)
		}
	}

	if len(errors) > 0 {
		for _, e := range errors {
			pf("error: %v string: %v char: %c unicode: %U \n", e, string(e), e, e)
		}
		// Pause()
	}
}
