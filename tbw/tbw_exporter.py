#!/usr/bin/env python3

"""A simple system of for Pāḷi word lookup consisting of:
1. inflection to headwords
2. dictionary data for EBTS.
3. compound deconstruction
"""

import json

from rich import print

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, Lookup
from tools.pali_sort_key import pali_sort_key
from tools.tic_toc import tic, toc
from tools.cst_sc_text_sets import make_sc_text_set
from tools.meaning_construction import make_meaning_html
from tools.meaning_construction import summarize_construction
from tools.paths import ProjectPaths


def main():
    tic()
    print("[bright_yellow]dpd lookup system for TBW")

    pth = ProjectPaths()

    # --------------------------------------------------
    # make a set of words in sutta central texts
    # --------------------------------------------------
    
    print(f"[green]{'making sutta central ebts word list':<40}", end="")
    sc_text_list = [
        "vin1", "vin2", "vin3", "vin4", "vin5",
        "dn1", "dn2", "dn3",
        "mn1", "mn2", "mn3",
        "sn1", "sn2", "sn3", "sn4", "sn5",
        "an1", "an2", "an3", "an4", "an5",
        "an6", "an7", "an8", "an9", "an10", "an11",
        "kn1", "kn2", "kn3", "kn4", "kn5",
        "kn8", "kn9",
        ]

    text_set: set = make_sc_text_set(pth, sc_text_list)
    print(f"{len(text_set):,}")

    # --------------------------------------------------
    # get all the required info from the database
    # --------------------------------------------------
    
    print(f"[green]{'making db searches':<40}", end="")

    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadwords)

    deconstr_db = db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
    print("OK")

    # --------------------------------------------------
    # make a set of all words in deconstructed compounds
    # --------------------------------------------------
    
    print(f"[green]{'making deconstructor splits set':<40}", end="")
    deconstr_splits_set: set = set()
    matched = set()
    for i in deconstr_db:
        if i.lookup_key in text_set:
            matched.add(i.lookup_key)
            deconstructions = i.deconstructor_unpack
            for deconstruction in deconstructions:
                deconstr_splits_set.update(deconstruction.split(" + "))
    print(f"{len(deconstr_splits_set):,}")

    # --------------------------------------------------
    # make an inflections to headwords dictionary
    # --------------------------------------------------
    
    print(f"[green]{'making inflections to headwords dict':<40}", end="")
    i2h: dict = {}
    for __counter__, i in enumerate(dpd_db):
        inflections = i.inflections_list
        for inflection in inflections:
            test1 = (
                inflection in text_set or
                inflection in deconstr_splits_set)
            test2 = "(gram)" not in i.meaning_1
            if test1 & test2:
                matched.add(inflection)
                if inflection not in i2h:
                    i2h[inflection] = [i.lemma_1]
                else:
                    i2h[inflection] += [i.lemma_1]
    print(f"{len(i2h):,}")

    # --------------------------------------------------
    # save inflections to headwords .js
    # --------------------------------------------------
    
    print(f"[green]{'writing inflections to headwords json':<40}", end="")
    i2h_json_dump = json.dumps(i2h, ensure_ascii=False, indent=2)
    with open(pth.i2h_js_path, "w") as f:
        f.write(f"dpd_i2h = {i2h_json_dump}")
        print("OK")

    # --------------------------------------------------
    # make a set of unmatched words
    # --------------------------------------------------
    
    print(f"[green]{'making set of unmatched words':<40}", end="")
    unmatched = text_set - matched
    print(f"{len(unmatched):,}")

    # --------------------------------------------------
    # make a set of headwords in ebts
    # --------------------------------------------------
    
    print(f"[green]{'making headwords set':<40}", end="")
    headwords_set: set = set()
    for __key__, values in i2h.items():
        headwords_set.update(values)
    print(f"{len(headwords_set):,}")

    # --------------------------------------------------
    # make a dict of dpd data - only words in ebts
    # --------------------------------------------------
    
    print(f"[green]{'making dpd ebts dict':<40}", end="")
    dpd_dict = {}
    for i in dpd_db:
        if i.lemma_1 in headwords_set:
            string = f"{i.pos}. "
            string += make_meaning_html(i)
            if i.construction:
                string += f" [{summarize_construction(i)}]"
            dpd_dict[i.lemma_1] = string

    dpd_dict = dict(
        sorted(dpd_dict.items(), key=lambda x: pali_sort_key(x[0])))
    print(f"{len(dpd_dict):,}")

    # --------------------------------------------------
    # write dpd dict to .js
    # --------------------------------------------------
    
    print(f"[green]{'writing dpd ebts to json':<40}", end="")
    dpd_json_dump = json.dumps(dpd_dict, ensure_ascii=False, indent=2)
    with open(pth.dpd_ebts_js_path, "w") as f:
        f.write(f"let dpd_ebts = {dpd_json_dump}")
        print("OK")

    # --------------------------------------------------
    # make a dict of all deconstructed compounds
    # --------------------------------------------------
    
    print(f"[green]{'making deconstructor dict':<40}")
    deconstr_dict = {}
    for i in deconstr_db:
        if (
            i.lookup_key not in dpd_dict and
            i.lookup_key in text_set
        ):
            deconstructions = i.deconstructor_unpack
            string = "<br>".join(deconstructions)
            deconstr_dict[i.lookup_key] = string


    # --------------------------------------------------
    # add variant readings to decosntructor data
    # --------------------------------------------------
    
    print("[green]adding variants")
    variants_db = db_session \
        .query(Lookup) \
        .filter(Lookup.variant != "") \
        .all()

    for i in variants_db:
        if i.lookup_key in text_set:
            variant_string = f"variant reading of <i>{i.variants_unpack[0]}</i>"
            if i.lookup_key in deconstr_dict:
                deconstr_dict[i.lookup_key] += f"<br>{variant_string}"
            else:
                deconstr_dict[i.lookup_key] = variant_string
    
    # --------------------------------------------------
    # add spelling mistakes to decosntructor data
    # --------------------------------------------------

    print("[green]adding spelling mistakes")
    spelling_db = db_session \
        .query(Lookup) \
        .filter(Lookup.spelling != "") \
        .all()

    for i in spelling_db:
        if i.lookup_key in text_set:
            spelling_string = f"incorrect spelling of <i>{i.spelling_unpack[0]}</i>"
            if i.lookup_key in deconstr_dict:
                deconstr_dict[i.lookup_key] += f"<br>{spelling_string}"
            else:
                deconstr_dict[i.lookup_key] = spelling_string

    # --------------------------------------------------
    # sort deconstructor dict
    # --------------------------------------------------
    
    print(f"[green]{'sorting deconstructor dict':<40}", end="")
    deconstr_dict = dict(
        sorted(deconstr_dict.items(), key=lambda x: pali_sort_key(x[0])))
    print(f"{len(deconstr_dict):,}")

    # --------------------------------------------------
    # save deconstr dict to .js
    # --------------------------------------------------
    
    print(f"[green]{'writing deconstructor dict to json':<40}", end="")
    json_dump = json.dumps(deconstr_dict, ensure_ascii=False, indent=2)
    with open(pth.deconstructor_js_path, "w") as f:
        f.write(f"let dpd_deconstructor = {json_dump}")
        print("OK")

    toc()


if __name__ == "__main__":
    main()
