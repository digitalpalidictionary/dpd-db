# style guideline

## dpd_headwords table

### lemma_1

- Provide the dictionary form of the word.
- If the same word comes from different roots, use the numbering system (e.g., 1.1, 2.1, etc.).
- If words come from the same root but have different meanings, use the numbering system (e.g., 1.1, 1.2, etc.).
- If a word has clear different meanings in context, add a new number and meaning.
- If a word has different case relationships in different sentences (e.g., +acc in one, +dat in another), list the meanings separately.

### lemma_2

- Present clean Pāli without numbers.
- Neuter nouns that end in -a in Pali_1 will have -aṃ ending in Pali_2 (e.g., Pali_1: citta 1.1, Pali_2: cittaṃ).
- Masculine nouns that end in -a in Pali_1 will have -o ending in Pali_2 (e.g., Pali_1: dhamma 1.01, Pali_2: dhammo).
- Prefixes will have a hyphen (-) at the end of the prefix (e.g., saṃ-).
- Suffixes will have a hyphen (-) at the beginning of the suffix (e.g., -dhā).

### pos

- Indicate the part of speech for the given term.
- Refer to the possibilities outlined in [tools/pos.py](https://github.com/digitalpalidictionary/dpd-db/blob/main/tools/pos.py)

### grammar

- Provide various grammatical information for the term.
- If the noun (masc/fem/nt) originally comes from another part of speech (POS), mention it, e.g., "pp of $derived_from," "prp of $derived_from," "ptp of $derived_from."
- For adj, avoid mentioning "pp of $derived_from," "prp of $derived_from," "ptp of $derived_from." However, it can be noted as "app of $derived_from."
- For idioms, mention the components from which it is composed (e.g., idiom, adv + ind + ind).
- For pr, specify if it is derived from a causative or passive form, e.g., "caus of $derived_from," "pass of $derived_from." 
- If a pr is formed from a passive base and then adds a causative suffix added, mention "pass of $derived_from," and in the field "verb" mention "caus"
- If a pr is formed from a causative base and then adds a passive suffix added, mention "caus of $derived_from," and in the field "verb" mention "pass"

### derived_from

- Word from which the lemma_1 is derived.
- (or) Combination of ruut and prefix(es) from which the lemma_1 is derived.

### neg

- Indicate "neg" if the term is a negative word, has ne.g. prefix (e.g., na-, vi-).
- If the word has two negative prefixes, indicate "ne.g. x2."

### verb

- For all parts of speech except present tense (pr), variations include "", "caus", "pass"
- For present tense (pr) this information splitted between this field and "grammar" field
- If the $derived_from verb is denominative mention 'deno'
- If the $derived_from verb is desiderative mention 'desid'
- If the verb, verbal participles, indeclinable participles, idiom or sandhi is impersonal mention 'impers'
- Those variation can be combined, (e.g. 'impers, pass' or 'caus, pass')

### trans

- "trans" for all verbs and verbal participles that take a direct object (+acc).
- "intrans" for all verbs and verbal participles that do not take a direct object (+acc) or take it with different clase (e.g. +instr).
- "ditrans" if the verb or verbal participle takes two (or more) objects.

### plus_case

- Specify the case in which the object of the verb or verbal participle appears.
- If word takes infinitive mention "+inf"

### meaning_1

- English meaning of the word within the context of the given example(s).
- Include a few synonyms in order of importance.

### meaning_lit

- Literal meaning of the word, where relevant.

### meaning_2

- Meaning sourced from original dictionaries (e.g., Buddhadatta dictionary, etc.).

### non_ia


### sanskrit	

- Closest Sanskrit cognate of the headword
- See [explicit guide](https://github.com/digitalpalidictionary/dpd-db/blob/main/db/db/sanskrit/sanskrit_style_guide.md)

### root_key

- The root_key divided by meanings, should be chosen from existing in dpd_roots table

### root_sign

- The conjugational sign determining to which root group this root belongs.

<br/>Root Groups:
<br/>1  √bhū etc. (+ a) bhūvāddigaṇa
<br/>2  √rudh etc. (+ ṃ-a) rudhādigaṇa 
<br/>3  √div etc. (+ ya) divādigaṇa 
<br/>4  √su etc. (+ ṇo + ṇā + uṇā) svādigaṇa 
<br/>5  √ki etc. (+ nā) kiyādigaṇa
<br/>6  √gah etc. (+ ṇhā) gahādigaṇa
<br/>7  √tan etc. (+ o) tanādigaṇa
<br/>8  √cur etc. (+ *e + *aya) curādigaṇa"

- For causative, signs can be *aya, *ala, *e, *āpaya, *āpe.
- For passive, signs can be iya, ya, īya.
- For causative-passive, signs can be combinations of causative and passive signs (e.g., *e + iya, *āpe + iya, ya + *aya, ya + *e, ya + *āpe). 
- Sometimes, it can be a combined sign of the root group and causative/passive sign (e.g., ṃa + *āpe + īya).

### root_base

- Root + Conjugational sign > Base.
- Includes information about causative, passive, denominative, future, irregular, and desiderative forms.

### family_root

- All words which are formed from the same prefix + root combination
- Indicate to which family of prefix(es) + root this word belongs.

### family_word

- All words comprised of the same component word

### family_compound

- All words comprised of the same component word
- Mention parts of compounds in dictionary form.
- If some part does not exist in DPD, please add it as a new word.

### construction

- For words derived from a root, e.g. <b>na > a + √kar + ta + tta</b> :
<br/>prefix(es) + root or base + primary derivative + secondary derivative(s) + case endings
<br/>
- for secondary derivative add second line where showing its formation (e.g. <b>na > a + √kaṅkh + ā + ī<b><br>
<b>akaṅkhā + ī<b>)
- For compound words, e.g. <b>abhi + okāsa + *ika</b> :
<br/>component word 1 + component word 2 + secondary derivative(s) + case endings

### derivative

- Type of derivative and (the derivative itself), e.g. <b>kita (ta)</b>
- - <b>kita</b> – primary derivative
- - <b>kiccha</b> – primary derivative forming potential participles
- - <b>taddhita</b> – secondary derivative

### suffix

- Last suffix which determin type of derivative

### phonetic

- Phonetic changes undergone by vowels and consonants, e.g. <b>rt > t</b>

### compound_type

- Type of compound in Pāli
- For bahubbīhi compounds, mention from which compound type it originated  (e.g. 'digu > bahubbīhi')

### compound_construction

- Expanded construction of the compound
- Bold the declined part of the component (e.g. akat<b>aṃ</b> + ñū)

### non_root_in_comps


### source_1 and source_2

- Sutta number for example # 1 and 2  (DPR Quick Link)
- Do not use space between book and sutta number (e.g. SN11.1)

### sutta_1 and sutta_2

- Name of the sutta for example # 1 and 2
- Usually from Chaṭṭha Saṅgāyana corpus

### example_1 and example_1

- Relevant example # 1 and 2 of the headword in context.
- Bold lemma_1 in its inflected form
- Try to avoid `-`, exeptions may be only very long compounds. (e.g. cīvara-piṇḍapāta-sen'āsana-gilānapaccaya-bhesajjaparikkhārehi)

### antonym

- Word with the opposite meaning in context.

### synonym

- Word with a similar meaning in context.

### variant

- Different form of the same word, either by morphology, different spelling, or a variant reading found in texts

### commentary

- Meaning in context according to the Aṭṭhakathā or Ṭīkā
- Bold the $lemma_1

### notes

- Notes, comments and information from other sources

### cognate


### family_set

- Different categories of words

### stem

- Non-declined part of the word, without declined ending
- Starting with `!` for not dictionary forms
- * for irregular declinations
- `-` for indeclinables

### pattern

- Pattern by which the word changes its inflected forms.
- All patterns can be found in the [inflection_templates.xlsx](https://github.com/digitalpalidictionary/dpd-db/raw/main/db/inflections/inflection_templates.xlsx)











