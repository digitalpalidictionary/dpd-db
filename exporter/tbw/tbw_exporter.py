#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A simple system of for Pāḷi word lookup consisting of:
1. inflection to headwords
2. dictionary data for EBTS.
3. compound deconstruction

Export to `TBW2` and `fdg_dpd` repos
"""

import json

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.configger import config_test
from tools.cst_sc_text_sets import make_sc_text_set
from tools.meaning_construction import make_meaning_combo_html
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class ProgData:
    def __init__(self) -> None:
        pr.green("setting up data")
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        dpd_db = self.db_session.query(DpdHeadword)
        self.dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))
        self.deconstructor_db = (
            self.db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
        )
        self.variants_db = (
            self.db_session.query(Lookup).filter(Lookup.variant != "").all()
        )
        self.spelling_db = (
            self.db_session.query(Lookup).filter(Lookup.spelling != "").all()
        )
        self.word_set: set[str] = set()
        self.deconstructed_splits_set: set[str] = set()
        self.matched_set: set[str] = set()
        self.i2h_dict: dict[str, list[str]] = {}
        self.unmatched_set: set[str] = set()
        self.headwords_set: set[str] = set()
        self.dpd_dict: dict[str, str] = {}
        self.deconstructor_dict: dict[str, str] = {}
        pr.yes("ok")


def generate_sc_word_set(g: ProgData):
    sc_text_list = [
        "vin1",
        "vin2",
        "vin3",
        "vin4",
        "vin5",
        "dn1",
        "dn2",
        "dn3",
        "mn1",
        "mn2",
        "mn3",
        "sn1",
        "sn2",
        "sn3",
        "sn4",
        "sn5",
        "an1",
        "an2",
        "an3",
        "an4",
        "an5",
        "an6",
        "an7",
        "an8",
        "an9",
        "an10",
        "an11",
        "kn1",
        "kn2",
        "kn3",
        "kn4",
        "kn5",
        "kn8",
        "kn9",
    ]

    sc_word_set = make_sc_text_set(g.pth, sc_text_list)
    g.word_set = sc_word_set


def generate_deconstructed_word_set(g: ProgData):
    """make a set of all words in deconstructed compounds"""

    pr.green("making deconstructor splits set")
    for i in g.deconstructor_db:
        if i.lookup_key in g.word_set:
            g.matched_set.add(i.lookup_key)
            deconstructions = i.deconstructor_unpack
            for deconstruction in deconstructions:
                g.deconstructed_splits_set.update(deconstruction.split(" + "))
    pr.yes(len(g.deconstructed_splits_set))


def generate_i2h_dict(g: ProgData):
    """make an inflections to headwords dictionary"""

    pr.green("making inflection2headwords dict")
    for __counter__, i in enumerate(g.dpd_db):
        inflections = i.inflections_list_all  # include api ca eva iti
        for inflection in inflections:
            test1 = inflection in g.word_set or inflection in g.deconstructed_splits_set
            test2 = "(gram)" not in i.meaning_1
            if test1 & test2:
                g.matched_set.add(inflection)
                if inflection not in g.i2h_dict:
                    g.i2h_dict[inflection] = [i.lemma_1]
                else:
                    g.i2h_dict[inflection] += [i.lemma_1]
    pr.yes(len(g.i2h_dict))


def sort_i2h_dict(g: ProgData):
    """sort i2h dict by values"""

    pr.green("sorting i2h_dict")
    for inflection, headwords in g.i2h_dict.items():
        g.i2h_dict[inflection] = pali_list_sorter(headwords)
    pr.yes(len(g.i2h_dict))


def generate_unmatched_word_set(g: ProgData):
    """make a set of unmatched words"""

    pr.green("making set of unmatched words")
    g.unmatched_set = g.word_set - g.matched_set
    pr.yes(len(g.unmatched_set))


def generate_ebt_headwords_set(g: ProgData):
    """make a set of headwords in ebts"""

    pr.green("making headwords set")
    for __key__, values in g.i2h_dict.items():
        g.headwords_set.update(values)
    pr.yes(len(g.headwords_set))


def generate_dpd_ebt_dict(g: ProgData):
    """make a dict of dpd data - only words in ebts"""

    pr.green("making dpd ebts dict")
    for i in g.dpd_db:
        if i.lemma_1 in g.headwords_set:
            string = ""
            string = f"{i.pos}. "
            string += make_meaning_combo_html(i)
            if i.construction:
                string += f" [{i.construction_summary}]"
            g.dpd_dict[i.lemma_1] = string

    g.dpd_dict = dict(sorted(g.dpd_dict.items(), key=lambda x: pali_sort_key(x[0])))
    pr.yes(len(g.dpd_dict))


def generate_deconstructor_dict(g: ProgData):
    """make a dict of all deconstructed compounds"""

    pr.green("making deconstructor dict")

    for i in g.deconstructor_db:
        if i.lookup_key not in g.dpd_dict and i.lookup_key in g.word_set:
            deconstructions = i.deconstructor_unpack
            string = "<br>".join(deconstructions)
            g.deconstructor_dict[i.lookup_key] = string
    pr.yes(len(g.deconstructor_dict))


def deconstructor_dict_add_variants(g: ProgData):
    """add variant readings to deconstructor data"""

    pr.green("adding variants")
    var_counter = 0
    for i in g.variants_db:
        if i.lookup_key in g.word_set:
            variant_string = f"variant reading of <i>{i.variants_unpack[0]}</i>"
            if i.lookup_key in g.deconstructor_dict:
                g.deconstructor_dict[i.lookup_key] += f"<br>{variant_string}"
                var_counter += 1
            else:
                g.deconstructor_dict[i.lookup_key] = variant_string
                var_counter += 1
    pr.yes(var_counter)


def deconstructor_dict_add_spelling_mistakes(g: ProgData):
    """add spelling mistakes to deconstructor data"""

    pr.green("adding spelling mistakes")
    spell_counter = 0
    for i in g.spelling_db:
        if i.lookup_key in g.word_set:
            spelling_string = f"incorrect spelling of <i>{i.spelling_unpack[0]}</i>"
            if i.lookup_key in g.deconstructor_dict:
                g.deconstructor_dict[i.lookup_key] += f"<br>{spelling_string}"
                spell_counter += 1
            else:
                g.deconstructor_dict[i.lookup_key] = spelling_string
                spell_counter += 1
    pr.yes(spell_counter)


def sort_deconstructor_dict(g: ProgData):
    """sort deconstructor dict"""

    pr.green("sorting deconstructor dict")
    g.deconstructor_dict = dict(
        sorted(g.deconstructor_dict.items(), key=lambda x: pali_sort_key(x[0]))
    )
    pr.yes(len(g.deconstructor_dict))


def save_js_files_for_tbw(g: ProgData):
    """saving .js files for tbw"""

    pr.green("saving .js files for tbw")

    i2h_json_dump = json.dumps(g.i2h_dict, ensure_ascii=False, indent=2)
    with open(g.pth.tbw_i2h_js_path, "w") as f:
        f.write(f"dpd_i2h = {i2h_json_dump}")

    dpd_json_dump = json.dumps(g.dpd_dict, ensure_ascii=False, indent=2)
    with open(g.pth.tbw_dpd_ebts_js_path, "w") as f:
        f.write(f"let dpd_ebts = {dpd_json_dump}")

    json_dump = json.dumps(g.deconstructor_dict, ensure_ascii=False, indent=2)
    with open(g.pth.tbw_deconstructor_js_path, "w") as f:
        f.write(f"let dpd_deconstructor = {json_dump}")

    pr.yes("ok")


def save_js_files_for_fdg(g: ProgData):
    """saving .js files for fdg"""

    pr.green("saving .js files for fdg")

    i2h_json_dump = json.dumps(g.i2h_dict, ensure_ascii=False, indent=2)
    with open(g.pth.fdg_i2h_js_path, "w") as f:
        f.write(f"dpd_i2h = {i2h_json_dump}")

    dpd_json_dump = json.dumps(g.dpd_dict, ensure_ascii=False, indent=2)
    with open(g.pth.fdg_dpd_ebts_js_path, "w") as f:
        f.write(f"let dpd_ebts = {dpd_json_dump}")

    json_dump = json.dumps(g.deconstructor_dict, ensure_ascii=False, indent=2)
    with open(g.pth.fdg_deconstructor_js_path, "w") as f:
        f.write(f"let dpd_deconstructor = {json_dump}")

    pr.yes("ok")


# FIXME cleanup when tested
# def save_json_files_for_sc(g: ProgData):
#     """Copy json files to sc-data dir"""

#     pr.green("copying json files to sc-data")

#     with open(g.pth.sc_i2h_json_path, "w") as f:
#         json.dump(g.i2h_dict, f, ensure_ascii=False, indent=2)

#     with open(g.pth.sc_dpd_ebts_json_path, "w") as f:
#         json.dump(g.dpd_dict, f, ensure_ascii=False, indent=2)

#     with open(g.pth.sc_deconstructor_json_path, "w") as f:
#         json.dump(g.deconstructor_dict, f, ensure_ascii=False, indent=2)

#     pr.yes("ok")


def main():
    pr.tic()
    pr.title("export dpd data for TBW and FDG")

    if not config_test("exporter", "make_tbw", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    g = ProgData()
    generate_sc_word_set(g)
    generate_deconstructed_word_set(g)
    generate_i2h_dict(g)
    sort_i2h_dict(g)
    generate_unmatched_word_set(g)
    generate_ebt_headwords_set(g)
    generate_dpd_ebt_dict(g)
    generate_deconstructor_dict(g)
    # deconstructor_dict_add_variants(g) # format has changed
    deconstructor_dict_add_spelling_mistakes(g)
    sort_deconstructor_dict(g)

    save_js_files_for_tbw(g)
    save_js_files_for_fdg(g)
    # FIXME cleanup when tested
    # save_json_files_for_sc(g)

    pr.toc()


if __name__ == "__main__":
    main()
