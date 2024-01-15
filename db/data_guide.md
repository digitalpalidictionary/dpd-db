# PaliWord table style guideline

### pali_1

- Provide the dictionary form of the word.
- If the same word comes from different roots, use the numbering system (e.g., 1.1, 2.1, etc.).
- If words come from the same root but have different meanings, use the numbering system (e.g., 1.1, 1.2, etc.).
- If a word has clear different meanings in context, add a new number and meaning.
- If a word has different case relationships in different sentences (e.g., +acc in one, +dat in another), list the meanings separately.

### pali_2

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

- Word or root from which the term is derived.

### neg

- Indicate "neg" if the term is a negative word, has neg prefix (e.g., na-, vi-).
- If the word has two negative prefixes, indicate "neg x2."

### verb

- For all parts of speech except present tense (pr), variations include "", "caus," "pass," "caus, pass."
- For present tense (pr) this information splitted between this field and "grammar" field

### trans

- "trans" for all verbs and verbal participles that take a direct object (+acc).
- "intrans" for all verbs and verbal participles that do not take a direct object (+acc) or take it with different clase (eg +instr).
- "ditrans" if the verb or verbal participle takes two (or more) objects.

### plus_case

- Specify the case in which the object of the verb or verbal participle appears.
- if word takes infinitive mention "+inf"

### meaning_1

- English meaning of the word within the context of the given example(s).
- Include a few synonyms in order of importance.

### meaning_lit

- Literal meaning of the word, where relevant.

### meaning_2

- Meaning sourced from original dictionaries (e.g., Buddhadatta dictionary, etc.).

### non_ia


### root_key

- The root_key divided by meanings.

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


### family_root


### family_word


### family_compound


### construction


### derivative


### suffix


### phonetic


### compound_type


### compound_construction


### non_root_in_comps


### source_1


### sutta_1


### example_1


### source_2


### sutta_2


### example_2


### antonym


### synonym


### variant


### commentary


### notes


### cognate


### family_set


### stem



### pattern



