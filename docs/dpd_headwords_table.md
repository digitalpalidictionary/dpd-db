# DPD Headwords table - columns and properties

Most of the database functionality comes from the 

```
class DpdHeadword(Base):
    __tablename__ = "dpd_headwords"
```

This can be found in the db model [here](../db/models.py).

- **columns** in the table are in bold,     
- [data type\] is in square brackets, 
- *derived properties* are in italics, 
- a brief description of the column or property follows

Here is a quick overview:

- **id** [int] unique numerical identifier for each word  

- **lemma_1** [str] unique headword and number

- *lemma_clean* [str] lemma_1 without any trailing digits

- *lemma_1_* [str] lemma_1 with underscores instead of spaces for use in code

- *lemma_link* [str] lemma_1 with %20 instead of spaces for website links

- *lemma_ipa* [str] lemma_clean in International Phonetic Alphabet

- *lemma_tts* [str] lemma_clean in International Phonetic Alphabet suitable for Text-to-Speech engines

- *lemma_trad* [str] form of the lemma found in traditional Pāḷi grammars

- *lemma_si* [str] form of the lemma found in traditional Pāḷi grammars, in Sinhala script

- **lemma_2** [str] masculine nominative singular of the headword for nouns

- **pos** [str] part of speech 

- *pos_list* [list] list of all the parts of speech in the database

- *pos_si* [str] part of speech translated into Sinhala 

- *pos_si_full* [str] part of speech translated into Sinhala, unabbreviated

- **grammar** [str] grammatical information

- **derived_from** [str] etymological parent from which the headword is derived 

- **neg** [str] is the headword a negative or double negative? 

- **verb** [str] is the verb causative, passive or denominative?

- **trans** [str] is the verb transitive, intransitive, or ditransitive?

- **plus_case** [str] what syntactical case does the word trigger?

- **plus_case_si** [str] what syntactical case does the word trigger, translated into Sinhala?

- **meaning_1** [str] what is the contextual meaning in English?

- **meaning_lit** [str] what is the literal meaning in English?

- **meaning_2** [str] what meaning does Buddhadatta give?

- *meaning_combo* [str] composite of meaning_1, meaning_lit and meaning_2

- *meaning_combo_html* [str] composite of meaning_1, meaning_lit and meaning_2 with meaning_1 in HTML <b\> tags

- *meaning_si* [str] meaning_1 translated into Sinhala

- **non_ia** [str] what non Indo-Aryan word is the headword derived from?

- **sanskrit** [str] what is the closest Sanskrit cognate in Monier-Williams or Edgerton?

- *sanskrit_clean* [str] what is the Sanskrit stripped of all content in [square brackets]?

- **root_key** [str] what is the unique root key in `dpd_roots` table?

- *root_clean* [str] what is the root_key without any trailing digits?

- *root_count* [int] how many times does the root_key occur in the database?

- **root_sign** [str] what is the conjugational sign of the root?

- **root_base** [str] what is the root and conjugational sign combined?

- *root_base_clean* [str] what is the root_base stripped of all phonetic changes?

- **family_root** [str] what are the prefixes and root family?

- *root_family_key* [str] what is the root key and family root, space separated?

- **family_word** [str] if not a root, what is the word family? 

- **family_compound** [str] if a compound, what are the component words, space separated?

- *family_compound_list* [list] list of the family_compound values

- **family_idioms** [str] if an idiom, what are the component words, space separated?

- *family_idioms_list* [list] list of the family_idioms values

- **family_set** [str] what set does the word belong to?

- *family_set_list* [list] list of the family_set values

- **construction** [str] how is the word constructed?

- *construction_clean* [str] construction stripped of all phonetic changes

- *construction_summary* [str] summary of the construction in one line

- *construction_summary_si* [str] summary of the construction in one line, transliterated into Sinhala

- *construction_line1* [str] first line of the construction 

- **derivative** [str] is the word a kita, kicca or taddhita derivative?

- **suffix** [str] what is the kita, kicca or final taddhita suffix?

- **phonetic** [str] what phonetic changes occur?

- **compound_type** [str] if a compound, what type of compound is the headword?

- **compound_construction** [str] if a compound, how is the compound constructed? 

- **non_root_in_comps** [str] (mostly unused)

- **source_1** [str] what is the source of the first example ?

- *source_link_1* [str] source of the first example with an embedded HTML link

- **sutta_1** [str] from which sutta does the first example come?

- **example_1** [str] what is a good contextual example of the headword?

- **source_2** [str] what is the source of the second example?

- *source_link_1* [str] source of the second example with an embedded HTML link

- *source_link_sutta* [str] sutta code from example with an embedded HTML link

- **sutta_2** [str] from which sutta does the second example come?

- **example_2** [str] what is a good second example of the headword in context?

- *degree_of_completion* [str] how complete is a word's data?

- *degree_of_completion_html* [str] how complete is a word's data, embedded in html tags?

- **antonym** [str] what is the antonym of the headword, comma space separated?

- *antonym_list* [list] list of all the antonyms

- **synonym** [str] what are synonyms of the headword, comma space separated?

- *synonym_list* [list] list of all the synonyms

- **variant** [str] what are the variant readings of the headword found in other Pāḷi texts, comma space separated?

- *variant_list* [list] list of all the variants

- **var_phonetic** [str] (currently unused) what are other phonetic variants of the headword found in Pāḷi texts, comma space separated?

- **var_text** [str] (currently unused) what are the variant readings of the headword found in other Pāḷi texts, comma space separated?

- **commentary** [str] how does the commentary define the headword, new line separated?

- **notes** [str] what further information should be mentioned about the headword?

- **cognate** [str] what English cognates does the headword have?

- **link** [str] for plants, animals and historical characters what is the wikipedia link?

- **origin** [str] what is the origin of the headword's data?

- **stem** [str] what is the stem upon which the inflection pattern is built?

- **pattern** [str] what is the inflection pattern found in the `inflection_patterns` table?

- **created_at** [datetime] when was the headword created?

- **updated_at** [datetime] when was the headword updated?

- **inflections** [str] what inflected forms does the headword take, comma separated?

- *inflections_list* [list] list of inflections

- **inflections_api_ca_eva_iti** [str] what inflected forms can be found in sandhi compounds with api, ca, eva and iti, comma separated?

- *inflections_list_api_ca_eva_iti* [list] list of inflections found in sandhi compounds with api, ca, eva and iti

- *inflections_list_all* [list] list of all inflections, including those with api, ca, eva and iti

- **inflections_sinhala** [str] what are the inflected forms in Sinhala script, comma separated?

- *inflections_sinhala_list* [list] list if all inflections in Sinhala script

- **inflections_devanagari** [str] what are the inflected forms in Devanagari script, comma separated?

- *inflections_devanagari_list* [list] list of all inflections in Devanagari script

- **inflections_thai** [str] what are the inflected forms in Thai script, comma separated?

- *inflections_thai_list* [list] list of all inflections in Thai script

- **inflections_html** [str] inflection table of the headwords as HTML table

- **freq_html** [str] frequency map of the word in CST corpus as HTML table

- **ebt_count** [str] how many times does the word occur in early Buddhist texts?

- *needs_grammar_button* [bool] does the headword need a grammar button?

- *needs_example_button* [bool] does the headword needs an example button?

- *needs_examples_button* [bool] does the headword needs an examples button?

- *needs_conjugation_button* [bool] does the headword need a conjugations button?

- *needs_declension_button* [bool] does the headword need a declensions button?

- *needs_root_family_button* [bool] does the headword need a root family button?

- *needs_word_family_button* [bool] does the headword need a word family button?

- *needs_compound_family_button* [bool] does the headword need a compound family button?

- *needs_compound_families_button* [bool] does the headword need a compound families button?

- *needs_idioms_button* [bool] does the headword need an idioms button?

- *needs_set_button* [bool] does the headword need a set button?

- *needs_sets_button* [bool] does the headword need a sets button?

- *needs_frequency_button* [bool] does the headword need a frequency button?

- *cf_set* [set] set of all compound families in the database

- *idioms_set* [set] set of all the idioms in the database

- *\__repr\__* [str] quick overview of headword data

## Database Relationships

The `DpdHeadword` class has direct access to other tables in the database through relationships.

- **.rt** connects to the `dpd_roots` table
- **.fr** connects to the `family_roots` table
- **.fw** connects to the `family_words` table
- **.sbs** connects to the `SBS` table
- **.ru** connects to the `russian` table
- **.si** connects to the `sinhala` table
- **.it** connects to the `inflection_templates` table


