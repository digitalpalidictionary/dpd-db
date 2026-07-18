package main

import "testing"

func TestExtractVariantWords(t *testing.T) {
	tests := []struct {
		name  string
		entry string
		want  string
	}{
		{
			"simple",
			"mudiṅgasaddo → mutiṅgasaddo (bj) ",
			"mutiṅgasaddo",
		},
		{
			"multiple clauses",
			"pītakaṁ lohitakaṁ → pītaṁ lohitaṁ (si) | mañjiṭṭhakaṁ → mañjeṭṭhakaṁ (bj) ",
			"pītaṁ lohitaṁ mañjeṭṭhakaṁ",
		},
		{
			"semicolon alternates",
			"lambikaṁ → lapilakaṁ (bj); lampikaṁ (si) ",
			"lapilakaṁ lampikaṁ",
		},
		{
			"continuation clause without arrow",
			"katīnañcasikkhā → katīnaṁ sikkhā (bj) | katīnañca (s1-3) | katīnaṁ ca (pts1) ",
			"katīnaṁ sikkhā katīnañca katīnaṁ ca",
		},
		{
			"unbalanced parens keep no stray arrow",
			"(…) → na tveva tāva saccānubodho hoti) (bj)",
			"na tveva tāva saccānubodho hoti",
		},
		{
			"unclosed witness paren truncated",
			"vasi → vasī (sya1ed, sya2ed, pts1ed, pts2ed, mr mn92:16 [Selasutta]; snp4.16:875",
			"vasī",
		},
		{
			"unclosed paren in continuation clause",
			"sītavātakalitā → sītavātakadditakalitā (bj) | sītavātakalitā (sya1ed, sya2ed,",
			"sītavātakadditakalitā sītavātakalitā",
		},
		{
			"multi-word witness list stripped",
			"cakkhu → cakkhuṁ (bj, sya-all, pts-vp-pli1, mr) ",
			"cakkhuṁ",
		},
		{
			"sandhi apostrophe joins parts",
			"daharā apāpikā → daharāsa'pāpikā (bj); daharā apāvikā (sya1ed, sya2ed)",
			"daharāsapāpikā daharā apāvikā",
		},
		{
			"editorial note clause skipped",
			"saghānakā → idaṁ padaṁ cck, pts-vp-pli1 potthakesu",
			"",
		},
		{
			"english note with witness codes skipped",
			"ārocesuṁ → As per si. Not found in sya-all, pts-vp-pli1 editions",
			"",
		},
		{
			"citation tokens dropped",
			"x → dn33:194 [Saṅgītisutta/5. Pañcaka] vuttaṁ",
			"vuttaṁ",
		},
		{
			"verse slash becomes space",
			"y → sabbe khandhā tathāyatana, / dhātuyo saccato tayo; /",
			"sabbe khandhā tathāyatana, dhātuyo saccato tayo;",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := extractVariantWords(tt.entry)
			if got != tt.want {
				t.Errorf("extractVariantWords(%q) = %q, want %q", tt.entry, got, tt.want)
			}
		})
	}
}
