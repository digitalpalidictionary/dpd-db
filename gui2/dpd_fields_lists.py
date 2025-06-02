"""Centralized lists of DPD fields for different views and filters."""

"""
0. id
1. lemma_1
2. lemma_2
3. pos
4. grammar
5. derived_from
6. neg
7. verb
8. trans
9. plus_case
10. meaning_1
11. meaning_lit
12. meaning_2
13. non_ia
14. sanskrit
15. root_key
16. root_sign
17. root_base
18. family_root
19. family_word
20. family_compound
21. family_idioms
22. family_set
23. construction
24. derivative
25. suffix
26. phonetic
27. compound_type
28. compound_construction
29. non_root_in_comps
30. source_1
31. sutta_1
32. example_1
33. source_2
34. sutta_2
35. example_2
36. antonym
37. synonym
38. variant
39. var_phonetic
40. var_text
41. commentary
42. notes
43. cognate
44. link
45. origin
46. stem
47. pattern
48. created_at
49. updated_at
50. inflections
51. inflections_api_ca_eva_iti
52. inflections_sinhala
53. inflections_devanagari
54. inflections_thai
55. inflections_html
56. freq_data
57. freq_html
58. ebt_count
"""

ALL = [
    "id",
    "lemma_1",
    "lemma_2",
    "pos",
    "grammar",
    "derived_from",
    "neg",
    "verb",
    "trans",
    "plus_case",
    "meaning_1",
    "meaning_lit",
    "meaning_2",
    "non_ia",
    "sanskrit",
    "root_key",
    "root_sign",
    "root_base",
    "family_root",
    "family_word",
    "family_compound",
    "family_idioms",
    "family_set",
    "construction",
    "derivative",
    "suffix",
    "phonetic",
    "compound_type",
    "compound_construction",
    "non_root_in_comps",
    "source_1",
    "sutta_1",
    "example_1",
    "source_2",
    "sutta_2",
    "example_2",
    "antonym",
    "synonym",
    "variant",
    "var_phonetic",
    "var_text",
    "commentary",
    "notes",
    "cognate",
    "link",
    "origin",
    "stem",
    "pattern",
    "created_at",
    "updated_at",
    "inflections",
    "inflections_api_ca_eva_iti",
    "inflections_sinhala",
    "inflections_devanagari",
    "inflections_thai",
    "inflections_html",
    "freq_data",
    "freq_html",
    "ebt_count",
]


ROOT_FIELDS = [
    "id",
    "lemma_1",
    "lemma_2",
    "pos",
    "grammar",
    "derived_from",
    "neg",
    "verb",
    "trans",
    "plus_case",
    "meaning_1",
    "meaning_lit",
    "meaning_2",
    "non_ia",
    "sanskrit",
    "root_key",
    "root_sign",
    "root_base",
    "family_root",
    # "family_word",
    # "family_compound",
    # "family_idioms",
    "family_set",
    "construction",
    "derivative",
    "suffix",
    "phonetic",
    # "compound_type",
    # "compound_construction",
    # "non_root_in_comps",
    "source_1",
    "sutta_1",
    "example_1",
    "source_2",
    "sutta_2",
    "example_2",
    "antonym",
    "synonym",
    "variant",
    "var_phonetic",
    "var_text",
    "commentary",
    "notes",
    "cognate",
    "link",
    "origin",
    "stem",
    "pattern",
    "comment",
    # "created_at",
    # "updated_at",
    # "inflections",
    # "inflections_api_ca_eva_iti",
    # "inflections_sinhala",
    # "inflections_devanagari",
    # "inflections_thai",
    # "inflections_html",
    # "freq_data",
    # "freq_html",
    # "ebt_count",
]

COMPOUND_FIELDS = [
    "id",
    "lemma_1",
    "lemma_2",
    "pos",
    "grammar",
    "derived_from",
    "neg",
    # "verb",
    # "trans",
    "plus_case",
    "meaning_1",
    "meaning_lit",
    "meaning_2",
    "non_ia",
    "sanskrit",
    # "root_key",
    # "root_sign",
    # "root_base",
    # "family_root",
    # "family_word",
    "family_compound",
    "family_idioms",
    "family_set",
    "construction",
    "derivative",
    "suffix",
    "phonetic",
    "compound_type",
    "compound_construction",
    # "non_root_in_comps",
    "source_1",
    "sutta_1",
    "example_1",
    "source_2",
    "sutta_2",
    "example_2",
    "antonym",
    "synonym",
    "variant",
    # "var_phonetic",
    # "var_text",
    "commentary",
    "notes",
    "cognate",
    "link",
    "origin",
    "stem",
    "pattern",
    "comment",
]

WORD_FIELDS = [
    "id",
    "lemma_1",
    "lemma_2",
    "pos",
    "grammar",
    "derived_from",
    "neg",
    # "verb",
    # "trans",
    "plus_case",
    "meaning_1",
    "meaning_lit",
    "meaning_2",
    "non_ia",
    "sanskrit",
    # "root_key",
    # "root_sign",
    # "root_base",
    # "family_root",
    "family_word",
    "family_compound",
    "family_idioms",
    "family_set",
    "construction",
    "derivative",
    "suffix",
    "phonetic",
    # "compound_type",
    # "compound_construction",
    # "non_root_in_comps",
    "source_1",
    "sutta_1",
    "example_1",
    "source_2",
    "sutta_2",
    "example_2",
    "antonym",
    "synonym",
    "variant",
    "var_phonetic",
    "var_text",
    "commentary",
    "notes",
    "cognate",
    "link",
    "origin",
    "stem",
    "pattern",
    "comment",
    # "created_at",
    # "updated_at",
    # "inflections",
    # "inflections_api_ca_eva_iti",
    # "inflections_sinhala",
    # "inflections_devanagari",
    # "inflections_thai",
    # "inflections_html",
    # "freq_data",
    # "freq_html",
    # "ebt_count",
]

PASS1_FIELDS = [
    "lemma_1",
    "lemma_2",
    "pos",
    "grammar",
    "meaning_2",
    "root_key",
    "family_root",
    "root_sign",
    "root_base",
    "construction",
    "family_compound",
    "family_word",
    "stem",
    "pattern",
    "example_1",
    "translation_1",
    "example_2",
    "translation_2",
    "comment",
]

NO_CLONE_LIST = [
    "id",
    "lemma_1",
    "lemma_2",
    "source_1",
    "sutta_1",
    "example_1",
    "translation_1",
    "source_2",
    "sutta_2",
    "example_2",
    "translation_2",
]

NO_SPLIT_LIST = [
    # id is handled separately (new ID)
    # lemma_1 is handled separately (incremented)
    # "lemma_2",  # Should be regenerated based on new lemma_1 and pos
    "source_1",
    "sutta_1",
    "example_1",
    "translation_1",
    "source_2",
    "sutta_2",
    "example_2",
    "translation_2",
    "commentary",
    "notes",
    "antonym",
    "synonym",
    "variant",
    "var_phonetic",
    "var_text",
    "comment",
    "origin",
]
