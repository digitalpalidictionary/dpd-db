package tools

var Pth = struct {
	DpdBaseDir string

	DpdDb  string
	DpdCss string

	VariantReadings        string
	SpellingMistakes       string
	DeconManualCorrections string
	DeconExceptions        string
	SandhiRules            string

	AllInflectionsJson string
	MatchesDict        string
	NegInflections     string
	TextSet            string
	UnmatchedJson      string

	CstTxtTextDir     string
	CStXmlDir         string
	ScJsonTextDir     string
	BjtRomanJsonDir   string
	BjtRomanTxtDir    string
	SyaTextDir        string
	OtherPaliTextsDir string

	MatchesTsv          string
	UnMatchedTsv        string
	StatsTsv            string
	DeconstructorOutput string

	CstFileFreqMap string
	CstFreqMap     string
	CstWordList    string

	ScFileFreqMap string
	ScFreqMap     string
	ScWordList    string

	BjtFileFreqMap string
	BjtFreqMap     string
	BjtWordList    string

	SyaFileFreqMap string
	SyaFreqMap     string
	SyaWordList    string

	CstFileMap string
	ScFileMap  string
	BjtFileMap string
	SyaFileMap string

	CstTemplate      string
	ScTemplate       string
	BjtTemplate      string
	FreqTemplateHtml string
}{
	// dpd base dir
	DpdBaseDir: "",

	DpdDb:  "dpd.db",
	DpdCss: "exporter/goldendict/css/dpd.css",

	// shared data/deconstructor
	VariantReadings:        "shared_data/deconstructor/variant_readings.tsv",
	SpellingMistakes:       "shared_data/deconstructor/spelling_mistakes.tsv",
	DeconManualCorrections: "shared_data/deconstructor/manual_corrections.tsv",
	DeconExceptions:        "shared_data/deconstructor/exceptions.tsv",
	SandhiRules:            "shared_data/deconstructor/sandhi_rules.tsv",

	// frequency maps
	CstFileFreqMap: "shared_data/frequency/cst_file_freq.json",
	CstFreqMap:     "shared_data/frequency/cst_freq.json",
	CstWordList:    "shared_data/frequency/cst_wordlist.json",

	ScFileFreqMap: "shared_data/frequency/sc_file_freq.json",
	ScFreqMap:     "shared_data/frequency/sc_freq.json",
	ScWordList:    "shared_data/frequency/sc_wordlist.json",

	BjtFileFreqMap: "shared_data/frequency/bjt_file_freq.json",
	BjtFreqMap:     "shared_data/frequency/bjt_freq.json",
	BjtWordList:    "shared_data/frequency/bjt_wordlist.json",

	SyaFileFreqMap: "shared_data/frequency/sya_file_freq.json",
	SyaFreqMap:     "shared_data/frequency/sya_freq.json",
	SyaWordList:    "shared_data/frequency/sya_wordlist.json",

	// deconstructor assets
	AllInflectionsJson: "db/deconstructor/assets/all_inflections_set.json",
	MatchesDict:        "db/deconstructor/assets/matches_dict.json",
	NegInflections:     "db/deconstructor/assets/neg_inflections_set.json",
	TextSet:            "db/deconstructor/assets/text_set.json",
	UnmatchedJson:      "db/deconstructor/assets/unmatched_set.json",

	// Pali text files
	CstTxtTextDir:     "resources/tipitaka-xml/romn_txt",
	CStXmlDir:         "resources/tipitaka-xml/romn",
	ScJsonTextDir:     "resources/sc-data/sc_bilara_data/root/pli/ms",
	BjtRomanJsonDir:   "resources/bjt/public/static/roman_json/",
	BjtRomanTxtDir:    "resources/bjt/public/static/roman_txt/",
	SyaTextDir:        "resources/syāmaraṭṭha_1927",
	OtherPaliTextsDir: "resources/other_pali_texts",

	// file maps
	CstFileMap: "go_modules/frequency/file_maps/cst_file_map.json",
	ScFileMap:  "go_modules/frequency/file_maps/sc_file_map.json",
	BjtFileMap: "go_modules/frequency/file_maps/bjt_file_map.json",
	SyaFileMap: "go_modules/frequency/file_maps/sya_file_map.json",

	// templates

	FreqTemplateHtml: "go_modules/frequency/templates/frequency_template.html",

	// deconstructor output
	MatchesTsv:          "go_modules/deconstructor/output/matches.tsv",
	UnMatchedTsv:        "go_modules/deconstructor/output/unmatched.tsv",
	DeconstructorOutput: "go_modules/deconstructor/output/deconstructor_output.json",
	StatsTsv:            "go_modules/deconstructor/output/stats.tsv",
}
