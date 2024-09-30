package dpdDb

import (
	"dpd/go_modules/tools"
	"encoding/json"
	"regexp"
	"strings"
	"time"
)

type InflectionTemplate struct {
	Pattern string `gorm:"column:patten"`
	Like    string `gorm:"column:like"`
	Data    string `gorm:"column:data"`
}

func (InflectionTemplate) TableName() string {
	return "inflection_templates"
}

type DpdRoot struct {
	Root                  string    `gorm:"column:root"`
	RootInComps           string    `gorm:"column:root_in_comps"`
	RootHasVerb           string    `gorm:"column:root_has_verb"`
	RootGroup             int       `gorm:"column:root_group"`
	RootSign              string    `gorm:"column:root_sign"`
	RootMeaning           string    `gorm:"column:root_meaning"`
	SanskritRoot          string    `gorm:"column:sanskrit_root"`
	SanskritRootMeaning   string    `gorm:"column:sanskrit_root_meaning"`
	SanskritRootClass     string    `gorm:"column:sanskrit_root_class"`
	RootExample           string    `gorm:"column:root_example"`
	DhatupathaNum         string    `gorm:"column:dhatupatha_num"`
	DhatupathaRoot        string    `gorm:"column:dhatupatha_root"`
	DhatupathaPali        string    `gorm:"column:dhatupatha_pali"`
	DhatupathaEnglish     string    `gorm:"column:dhatupatha_english"`
	DhatumanjusaNum       int       `gorm:"column:dhatumanjusa_num"`
	DhatumanjusaRoot      string    `gorm:"column:dhatumanjusa_root"`
	DhatumanjusaPali      string    `gorm:"column:dhatumanjusa_pali"`
	DhatumanjusaEnglish   string    `gorm:"column:dhatumanjusa_english"`
	DhatumalaRoot         string    `gorm:"column:dhatumala_root"`
	DhatumalaPali         string    `gorm:"column:dhatumala_pali"`
	DhatumalaEnglish      string    `gorm:"column:dhatumala_english"`
	PaniniRoot            string    `gorm:"column:panini_root"`
	PaniniSanskrit        string    `gorm:"column:panini_sanskrit"`
	PaniniEnglish         string    `gorm:"column:panini_english"`
	Note                  string    `gorm:"column:note"`
	MatrixTest            string    `gorm:"column:matrix_test"`
	RootInfo              string    `gorm:"column:root_info"`
	RootMatrix            string    `gorm:"column:root_matrix"`
	RootRUMeaning         string    `gorm:"column:root_ru_meaning"`
	SanskritRootRUMeaning string    `gorm:"column:sanskrit_root_ru_meaning"`
	CreatedAt             time.Time `gorm:"column:created_at"`
	UpdatedAt             time.Time `gorm:"column:updated_at"`
	// PW                    []DpdHeadword `gorm:"foreignKey:RT"`
}

func (DpdRoot) TableName() string {
	return "dpd_roots"
}

type FamilyRoot struct {
	RootFamilyKey string `gorm:"column:root_family_key;primaryKey"`
	RootKey       string `gorm:"column:root_key;primaryKey"`
	RootFamily    string `gorm:"column:root_family;default:''"`
	RootMeaning   string `gorm:"column:root_meaning;default:''"`
	HTML          string `gorm:"column:html;default:''"`
	Data          string `gorm:"column:data;default:''"`
	Count         int    `gorm:"column:count;default:0"`
	RootRUMeaning string `gorm:"column:root_ru_meaning;default:''"`
	HTMLRU        string `gorm:"column:html_ru;default:''"`
	DataRU        string `gorm:"column:data_ru;default:''"`
}

func (FamilyRoot) TableName() string {
	return "family_root"
}

type FamilyCompound struct {
	CompoundFamily string `gorm:"column:compound_family"`
	Html           string `gorm:"column:html"`
	Data           string `gorm:"column:data"`
	Count          int    `gorm:"column:count"`
	HtmlRu         string `gorm:"column:html_ru"`
	DataRu         string `gorm:"column:data_ru"`
}

func (FamilyCompound) TableName() string {
	return "family_compound"
}

type DpdHeadword struct {
	ID                     int    `gorm:"column:id;primaryKey"`
	Lemma1                 string `gorm:"column:lemma_1;uniqueIndex"`
	Lemma2                 string `gorm:"column:lemma_2"`
	POS                    string `gorm:"column:pos"`
	Grammar                string `gorm:"column:grammar"`
	DerivedFrom            string `gorm:"column:derived_from"`
	Neg                    string `gorm:"column:neg"`
	Verb                   string `gorm:"column:verb"`
	Trans                  string `gorm:"column:trans"`
	PlusCase               string `gorm:"column:plus_case"`
	Meaning1               string `gorm:"column:meaning_1"`
	MeaningLit             string `gorm:"column:meaning_lit"`
	Meaning2               string `gorm:"column:meaning_2"`
	NonIA                  string `gorm:"column:non_ia"`
	Sanskrit               string `gorm:"column:sanskrit"`
	RootKey                string `gorm:"column:root_key"`
	RootSign               string `gorm:"column:root_sign"`
	RootBase               string `gorm:"column:root_base"`
	FamilyRoot             string `gorm:"column:family_root"`
	FamilyWord             string `gorm:"column:family_word"`
	FamilyCompound         string `gorm:"column:family_compound"`
	FamilyIdioms           string `gorm:"column:family_idioms"`
	FamilySet              string `gorm:"column:family_set"`
	Construction           string `gorm:"column:construction"`
	Derivative             string `gorm:"column:derivative"`
	Suffix                 string `gorm:"column:suffix"`
	Phonetic               string `gorm:"column:phonetic"`
	CompoundType           string `gorm:"column:compound_type"`
	CompoundConstruction   string `gorm:"column:compound_construction"`
	NonRootInComps         string `gorm:"column:non_root_in_comps"`
	Source1                string `gorm:"column:source_1"`
	Sutta1                 string `gorm:"column:sutta_1"`
	Example1               string `gorm:"column:example_1"`
	Source2                string `gorm:"column:source_2"`
	Sutta2                 string `gorm:"column:sutta_2"`
	Example2               string `gorm:"column:example_2"`
	Antonym                string `gorm:"column:antonym"`
	Synonym                string `gorm:"column:synonym"`
	Variant                string `gorm:"column:variant"`
	VarPhonetic            string `gorm:"column:var_phonetic"`
	VarText                string `gorm:"column:var_text"`
	Commentary             string `gorm:"column:commentary"`
	Notes                  string `gorm:"column:notes"`
	Cognate                string `gorm:"column:cognate"`
	Link                   string `gorm:"column:link"`
	Origin                 string `gorm:"column:origin"`
	Stem                   string `gorm:"column:stem"`
	Pattern                string `gorm:"column:pattern"`
	Inflections            string `gorm:"column:inflections"`
	InflectionsApiCaEvaIti string `gorm:"column:inflections_api_ca_eva_iti"`
	InflectionsSinhala     string `gorm:"column:inflections_sinhala"`
	InflectionsDevanagari  string `gorm:"column:inflections_devanagari"`
	InflectionsThai        string `gorm:"column:inflections_thai"`
	InflectionsHtml        string `gorm:"column:inflections_html"`
	FreqData               string `gorm:"column:freq_data"`
	FreqHtml               string `gorm:"column:freq_html"`
	EbtCount               int    `gorm:"column:ebt_count"`
}

func (DpdHeadword) TableName() string {
	return "dpd_headwords"
}

func (d DpdHeadword) LemmaClean() string {
	r := regexp.MustCompile(` \d.*`)
	return r.ReplaceAllString(d.Lemma1, "")
}

func (d DpdHeadword) InflectionsList() []string {
	return strings.Split(d.Inflections, ",")
}

func (d DpdHeadword) InflectionsListApiCaEvaIti() []string {
	return strings.Split(d.InflectionsApiCaEvaIti, ",")
}

func (d DpdHeadword) InflectionsListALl() []string {

	inflectionsListAll := []string{}

	if list := d.InflectionsList(); len(list) > 0 {
		inflectionsListAll = append(inflectionsListAll, list...)
	}

	if list := d.InflectionsListApiCaEvaIti(); len(list) > 0 {
		inflectionsListAll = append(inflectionsListAll, list...)
	}

	return inflectionsListAll
}

// Relationships
type DpdHeadwordWithRelations struct {
	DpdHeadword
	RootKeyID    uint `gorm:"foreignKey:root_key"`
	FamilyWordID uint `gorm:"foreignKey:family_word"`
	PatternID    uint `gorm:"foreignKey:pattern"`
}

type Lookup struct {
	Key           string `gorm:"column:lookup_key"`
	Headwords     string `gorm:"column:headwords"`
	Roots         string `gorm:"column:roots"`
	Deconstructor string `gorm:"column:deconstructor"`
	Variant       string `gorm:"column:variant"`
	Spelling      string `gorm:"column:spelling"`
	Grammar       string `gorm:"column:grammar"`
	Help          string `gorm:"column:help"`
	Abbrev        string `gorm:"column:abbrev"`
	Epd           string `gorm:"column:epd"`
	Rpd           string `gorm:"column:rpd"`
	Other         string `gorm:"column:other"`
	Sinhala       string `gorm:"column:sinhala"`
	Devanagari    string `gorm:"column:devanagari"`
	Thai          string `gorm:"column:thai"`
}

func (Lookup) TableName() string {
	return "lookup"
}

func (l *Lookup) DeconstructorPack(deconList []string) {
	deconJson, err := json.Marshal(deconList)
	tools.HardCheck(err)
	l.Deconstructor = string(deconJson)
}

func (l Lookup) DeconstructorUnpack() []string {
	deconList := []string{}
	err := json.Unmarshal([]byte(l.Deconstructor), &deconList)
	tools.HardCheck(err)
	return deconList
}
