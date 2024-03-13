#!/usr/bin/env python3

"""Create an html list of all words belonging to the same root family
and add to db."""


import re

from collections import defaultdict
from rich import print

from root_matrix import generate_root_matrix
from root_info import generate_root_info_html

from db.get_db_session import get_db_session
from db.models import DpdRoots, DpdHeadwords, FamilyRoot, Lookup

from scripts.anki_updater import family_updater

from tools.configger import config_test
from tools.lookup_is_another_value import is_another_value
from tools.meaning_construction import degree_of_completion
from tools.meaning_construction import clean_construction
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths
from tools.superscripter import superscripter_uni
from tools.tic_toc import tic, toc
from tools.update_test_add import update_test_add

from exporter.ru_components.tools.tools_for_ru_exporter import make_short_ru_meaning, ru_replace_abbreviations

from sqlalchemy.orm import joinedload


def main():
    tic()

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    if config_test("exporter", "language", "en"):
        lang = "en"
    elif config_test("exporter", "language", "ru"):
        lang = "ru"
    # add another lang here "elif ..." and 
    # add conditions if lang = "{your_language}" in every instance in the code.

    if lang == "en":
        dpd_db = db_session.query(DpdHeadwords).filter(
            DpdHeadwords.family_root != "").all()
    elif lang == "ru":
        dpd_db = db_session.query(DpdHeadwords).options(
            joinedload(DpdHeadwords.ru)).filter(
            DpdHeadwords.family_root != "").all()
            
    dpd_db = sorted(
        dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    roots_db = db_session.query(DpdRoots).all()
    roots_db = sorted(
        roots_db, key=lambda x: pali_sort_key(x.root))

    rf_dict, bases_dict = make_roots_family_dict_and_bases_dict(dpd_db)
    rf_dict = compile_rf_html(dpd_db, rf_dict, lang)
    add_rf_to_db(db_session, rf_dict)
    update_lookup_table(db_session)
    generate_root_info_html(db_session, roots_db, bases_dict)
    html_dict = generate_root_matrix(db_session)
    db_session.close()

    if config_test("anki", "update", "yes"):
        # root families
        anki_data_list = make_anki_data(pth, rf_dict)
        deck = ["Family Root"]
        family_updater(anki_data_list, deck)

        # root matrix
        anki_data_list = make_anki_matrix_data(pth, html_dict, db_session)
        deck = ["Root Matrix"]
        family_updater(anki_data_list, deck)

    toc()


def make_roots_family_dict_and_bases_dict(dpd_db):
    print("[green]extracting root families and bases", end=" ")
    rf_dict = {}
    bases_dict = {}
    for i in dpd_db:

        # compile root subfamilies
        family = i.root_family_key

        if family not in rf_dict:
            rf_dict[family] = {
                "root_key": i.root_key,
                "root_family": i.family_root,
                "root_meaning": i.rt.root_meaning,
                "headwords": [i.lemma_1],
                "html": "",
                "html_ru": "",
                "count": 1,
                "meaning": i.rt.root_meaning,
                "meaning_ru": i.rt.root_ru_meaning,
                "data": [],
                "anki": []
            }
        else:
            rf_dict[family]["headwords"] += [i.lemma_1]
            rf_dict[family]["count"] += 1

        # compile bases
        base = re.sub("^.+> ", "", i.root_base)

        if base:
            if i.root_key not in bases_dict:
                bases_dict[i.root_key] = {base}
            else:
                bases_dict[i.root_key].add(base)

    print(len(rf_dict))
    return rf_dict, bases_dict


def compile_rf_html(dpd_db, rf_dict, lang="en"):
    print("[green]compiling html")

    for __counter__, i in enumerate(dpd_db):
        family = i.root_family_key

        if i.lemma_1 in rf_dict[family]["headwords"]:
            if not rf_dict[family]["html"]:
                html_string = "<table class='family'>"
            else:
                html_string = rf_dict[family]["html"]

            meaning = make_meaning(i)
            html_string += "<tr>"
            html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
            html_string += f"<td><b>{i.pos}</b></td>"
            html_string += f"<td>{meaning} {degree_of_completion(i)}</td>"
            html_string += "</tr>"

            rf_dict[family]["html"] = html_string

            if lang == "ru" and i.ru:
                if not rf_dict[family]["html_ru"]:
                    html_string = "<table class='family_ru'>"
                else:
                    html_string = rf_dict[family]["html_ru"]

                ru_meaning = make_short_ru_meaning(i, i.ru)
                pos = ru_replace_abbreviations(i.pos)
                html_string += "<tr>"
                html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                html_string += f"<td><b>{pos}</b></td>"
                html_string += f"<td>{ru_meaning} {degree_of_completion(i)}</td>"
                html_string += "</tr>"

                rf_dict[family]["html_ru"] = html_string

            # data
            rf_dict[family]["data"].append(
                (i.lemma_1, i.pos, meaning))

            # anki data
            anki_family = f"<b>{i.family_root}</b> "
            anki_family += f"{i.rt.root_group} ({i.rt.root_meaning})"
            construction = clean_construction(i.construction)
            if not i.meaning_1:
                construction = f"-{construction}"
            rf_dict[family]["anki"].append(
                (anki_family, i.lemma_1, i.pos, meaning, construction))

    for rf in rf_dict:
        header = make_root_header(rf_dict, rf)
        rf_dict[rf]["html"] = header + rf_dict[rf]["html"] + "</table>"
        if lang == "ru":
            header_ru = make_root_header_ru(rf_dict, rf)
            rf_dict[rf]["html_ru"] = header_ru + rf_dict[rf]["html_ru"] + "</table>"
    return rf_dict


def make_root_header(rf_dict, rf):
    header = "<p class='heading underlined'>"
    if rf_dict[rf]["count"] == 1:
        header += "<b>1</b> word belongs to the root family "
    else:
        header += f"<b>{rf_dict[rf]['count']}</b> words belong to the root family "
    header += f"<b>{rf_dict[rf]['root_family']}</b> ({rf_dict[rf]['meaning']})</p>"
    return header


def make_root_header_ru(rf_dict, rf):
    header = "<p class='heading underlined'>"
    if rf_dict[rf]["count"] == 1:
        header += "<b>1</b> слово принадлежащее к семье корня "
    else:
        header += f"<b>{rf_dict[rf]['count']}</b> слова принадлежащие к семье корня "
    header += f"<b>{rf_dict[rf]['root_family']}</b> ({rf_dict[rf]['meaning_ru']})</p>"
    return header


def add_rf_to_db(db_session, rf_dict):
    print("[green]adding to db", end=" ")

    add_to_db = []

    for __counter__, rf in enumerate(rf_dict):
        
        root_family = FamilyRoot(
            root_family_key=rf,
            root_key=rf_dict[rf]["root_key"],
            root_family=rf_dict[rf]["root_family"],
            root_meaning=rf_dict[rf]["root_meaning"],
            html=rf_dict[rf]["html"],
            html_ru=rf_dict[rf]["html_ru"],
            count=len(rf_dict[rf]["headwords"]))
        root_family.data_pack(rf_dict[rf]["data"])

        add_to_db.append(root_family)

    db_session.execute(FamilyRoot.__table__.delete()) # type: ignore
    db_session.add_all(add_to_db)
    db_session.commit()

    print(len(rf_dict))


def update_lookup_table(db_session):
    """Add root keys data to lookuptable."""
    print("[green]adding roots to lookup table", end = " ")

    r2h_dict = defaultdict(set)
    roots_db = db_session.query(DpdRoots).all()
    for r in roots_db:
        r2h_dict[r.root_clean].add(r.root)
        r2h_dict[r.root_no_sign].add(r.root)
        r2h_dict[r.root].add(r.root)

    family_root_db = db_session.query(FamilyRoot).all()
    for r in family_root_db:
        r2h_dict[r.root_family].add(r.root_key)
        r2h_dict[r.root_family_clean].add(r.root_key)
        r2h_dict[r.root_family_clean_no_space].add(r.root_key)
    
    lookup_table = db_session.query(Lookup).all()
    results = update_test_add(lookup_table, r2h_dict)
    update_set, test_set, add_set = results

    # update test add
    for i in lookup_table:
        if i.lookup_key in update_set:
            i.roots_pack(pali_list_sorter(r2h_dict[i.lookup_key]))
        elif i.lookup_key in test_set:
            if is_another_value(i, "roots"):
                i.root = ""
            else:
                db_session.delete(i)                
    
    db_session.commit()

    # add
    add_to_db = []
    for inflection, root_keys in r2h_dict.items():
        if inflection in add_set:
            add_me = Lookup()
            add_me.lookup_key = inflection
            add_me.roots_pack(pali_list_sorter(root_keys))
            add_to_db.append(add_me)

    db_session.add_all(add_to_db)
    db_session.commit()

    print(len(r2h_dict))


def make_anki_data(pth: ProjectPaths, rf_dict):
    """Create anki_data_list for updating"""

    anki_data_list = []

    for i in rf_dict:
        html = "<table><tbody>"
        family, headword, pos, meaning, construction = "", "", "", "", ""
        for row in rf_dict[i]["anki"]:
            family, headword, pos, meaning, construction = row
            html += "<tr valign='top'>"
            html += "<div style='color: #FFB380'>"
            html += f"<td>{headword}</td>"
            html += f"<td><div style='color: #FF6600'>{pos}</div></td>"
            html += f"<td><div style='color: #FFB380'>{meaning}</td>"
            if construction.startswith("-"):
                construction = construction.lstrip("-")
                html += f"<td><div style='color: #421B01'>{construction}</div></td></tr>"
            else:
                html += f"<td><div style='color: #FF6600'>{construction}</div></td></tr>"

        html += "</tbody></table>"
        if len(html) > 131072:
            print(f"[red]{i} longer than 131072 characters")
        else:
            anki_data_list += [(family, html)]
    
    return anki_data_list


def make_anki_matrix_data(pth: ProjectPaths, html_dict, db_session):
    """Save root matrix data for anki updater"""

    anki_data_list = []

    for family, html in html_dict.items():
        db = db_session.query(DpdRoots).filter(DpdRoots.root == family).first()
        anki_name = f"{db.root_clean} {db.root_group} {db.root_meaning}"
        anki_data_list += [(anki_name, html)]
    
    return anki_data_list


if __name__ == "__main__":
    print("[bright_yellow]root families")
    if (
        config_test("exporter", "make_dpd", "yes") or 
        config_test("regenerate", "db_rebuild", "yes") or 
        config_test("exporter", "make_tpr", "yes") or 
        config_test("exporter", "make_ebook", "yes")
    ):
        main()
    else:
        print("generating is disabled in the config")
