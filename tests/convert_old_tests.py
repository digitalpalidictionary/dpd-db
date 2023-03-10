#!/usr/bin/env python_3.10

import csv
from helpers import InternalTestRow

column_names: dict = {
    "": "",
    "ID": "user_id",
    "Pāli1": "pali_1",
    "Pāli2": "pali_2",
    "Fin": "fin",
    "POS": "pos",
    "Grammar": "grammar",
    "Derived from": "derived_from",
    "Neg": "neg",
    "Verb": "verb",
    "Trans": "trans",
    "Case": "plus_case",
    "Meaning IN CONTEXT": "meaning_1",
    "Literal Meaning": "meaning_lit",
    "Non IA": "non_ia",
    "Sanskrit": "sanskrit",
    "Sk Root": "xxx_sanskrit_root",
    "Sk Root Mn": "xxx_sanskrit_root_meaning",
    "Cl": "xxx_sanskrit_root_class",
    "Pāli Root": "root_key",
    "Root In Comps": "xxx_root_in_comps",
    "V": "xxx_root_has_verb",
    "Grp": "xxx_root_group",
    "Sgn": "root_sign",
    "Root Meaning": "xxx_root_meaning",
    "Base": "root_base",
    "Family": "family_root",
    "Word Family": "family_word",
    "Family2": "family_compound",
    "Construction": "construction",
    "Derivative": "derivative",
    "Suffix": "suffix",
    "Phonetic Changes": "phonetic",
    "Compound": "compound_type",
    "Compound Construction": "compound_construction",
    "Non-Root In Comps": "non_root_in_comps",
    "Source1": "source_1",
    "Sutta1": "sutta_1",
    "Example1": "example_1",
    "Source 2": "source_2",
    "Sutta2": "sutta_2",
    "Example 2": "example_2",
    "Antonyms": "antonym",
    "Synonyms – different word": "synonym",
    "Variant – same constr or diff reading": "variant",
    "Commentary": "commentary",
    "Notes": "notes",
    "Cognate": "cognate",
    "Category": "family_set",
    "Link": "link",
    "Stem": "stem",
    "Pattern": "pattern",
    "Buddhadatta": "meaning_2",
}


def make_internal_tests_list():
    with open("tests/xxx old tests.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        internal_tests_list = [InternalTestRow(**row) for row in reader]
    return internal_tests_list


internal_tests_list = make_internal_tests_list()
for t in internal_tests_list:
    t.search_column_1 = column_names[t.search_column_1]
    t.search_column_2 = column_names[t.search_column_2]
    t.search_column_3 = column_names[t.search_column_3]
    t.search_column_4 = column_names[t.search_column_4]
    t.search_column_5 = column_names[t.search_column_5]
    t.search_column_6 = column_names[t.search_column_6]
    t.exceptions = ", ".join(t.exceptions)

with open("tests/internal_tests.tsv", mode="w", newline="") as csvfile:
    fieldnames = internal_tests_list[0].__dict__.keys()
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    for test in internal_tests_list:
        writer.writerow(test.__dict__)
