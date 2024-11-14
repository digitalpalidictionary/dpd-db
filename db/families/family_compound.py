#!/usr/bin/env python3

"""Compile compound families and save to database."""

import json
import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DbInfo, DpdHeadword, FamilyCompound

from scripts.build.anki_updater import family_updater


from tools.configger import config_test
from tools.meaning_construction import clean_construction
from tools.meaning_construction import degree_of_completion
from tools.meaning_construction import make_meaning_combo
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.superscripter import superscripter_uni
from tools.tic_toc import tic, toc

from exporter.goldendict.ru_components.tools.tools_for_ru_exporter import make_short_ru_meaning, ru_replace_abbreviations

from sqlalchemy.orm import joinedload


def main():
    tic()
    print("[bright_yellow]compound families generator")
    
    if not (
        config_test("exporter", "make_dpd", "yes") or 
        config_test("regenerate", "db_rebuild", "yes") or 
        config_test("exporter", "make_tpr", "yes") or 
        config_test("exporter", "make_ebook", "yes")
    ):
        print("[green]disabled in config.ini")
        toc()
        return

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db = db_session.query(DpdHeadword) \
        .options(joinedload(DpdHeadword.ru)) \
        .filter(DpdHeadword.family_compound != "") \
        .all()
    
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    cf_dict = create_comp_fam_dict(dpd_db)
    cf_dict = compile_cf_html(dpd_db, cf_dict)
    add_cf_to_db(db_session, cf_dict)
    update_db_cache(db_session, cf_dict)

    # update anki
    if config_test("anki", "update", "yes"):
        anki_data_list = make_anki_data(cf_dict)
        deck = ["Family Compound"]
        family_updater(anki_data_list, deck)
    

    toc()


def create_comp_fam_dict(dpd_db: list[DpdHeadword]):
    print("[green]extracting compound families and headwords", end=" ")

    # create a dict of all compound families
    # family: {headwords: [], html: "", }

    cf_dict: dict = {}

    for __counter__, i in enumerate(dpd_db):

        for cf in i.family_compound_list:
            if cf == " ":
                print("[bright_red]ERROR: spaces found please remove!")
            elif not cf:
                print("[bright_red]ERROR: '' found please remove!")
            elif cf == "+":
                print("[bright_red]ERROR: + found please remove!")

            test1 = re.findall(r"\bcomp\b", i.grammar) != []
            test2 = len(i.lemma_clean) < 30
            test3 = i.meaning_1

            if test1 and test2 and test3:

                if cf in cf_dict:
                    cf_dict[cf]["headwords"] += [i.lemma_1]
                else:
                    cf_dict[cf] = {
                        "headwords": [i.lemma_1],
                        "html": "",
                        "data": [],
                        "html_ru": "",
                        "data_ru": [],
                        "anki": []
                    }

    print(len(cf_dict))
    return cf_dict


def compile_cf_html(dpd_db, cf_dict):
    print("[green]compiling html")

    for __counter__, i in enumerate(dpd_db):

        for cf in i.family_compound_list:
            if cf in cf_dict:
                if i.lemma_1 in cf_dict[cf]["headwords"]:
                    if not cf_dict[cf]["html"]:
                        html_string = "<table class='family'>"
                    else:
                        html_string = cf_dict[cf]["html"]

                    meaning = make_meaning_combo(i)
                    
                    html_string += "<tr>"
                    html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                    html_string += f"<td><b>{i.pos}</b></td>"
                    html_string += f"<td>{meaning}</td>"
                    html_string += f"<td>{degree_of_completion(i)}</td>"
                    html_string += "</tr>"

                    cf_dict[cf]["html"] = html_string

                    # rus
                    if not cf_dict[cf]["html_ru"]:
                        ru_html_string = "<table class='family'>"
                    else:
                        ru_html_string = cf_dict[cf]["html_ru"]

                    ru_meaning = make_short_ru_meaning(i, i.ru)
                    pos = ru_replace_abbreviations(i.pos)
                    ru_html_string += "<tr>"
                    ru_html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                    ru_html_string += f"<td><b>{pos}</b></td>"
                    ru_html_string += f"<td>{ru_meaning}</td>"
                    ru_html_string += f"<td>{degree_of_completion(i)}</td>"
                    ru_html_string += "</tr>"

                    cf_dict[cf]["html_ru"] = ru_html_string

                    # data
                    if i.meaning_1:
                        cf_dict[cf]["data"].append((
                            i.lemma_1,
                            i.pos,
                            meaning,
                            degree_of_completion(i, html=False)
                        ))

                        # rus data
                        cf_dict[cf]["data_ru"].append((
                            i.lemma_1,
                            pos,
                            ru_meaning,
                            degree_of_completion(i, html=False)
                        ))

                    # anki data
                    if i.meaning_1:
                        construction = clean_construction(
                            i.construction) if i.meaning_1 else ""
                        cf_dict[cf]["anki"] += [
                            (i.lemma_1, i.pos, meaning, construction)]

    for i in cf_dict:
        cf_dict[i]["html"] += "</table>"
        cf_dict[i]["html_ru"] += "</table>"

    return cf_dict


def add_cf_to_db(db_session, cf_dict):
    print("[green]adding to db", end=" ")

    add_to_db = []

    for __counter__, cf in enumerate(cf_dict):
        cf_data = FamilyCompound(
            compound_family=cf,
            html=cf_dict[cf]["html"],
            html_ru=cf_dict[cf]["html_ru"],
            count=len(cf_dict[cf]["headwords"]))
        cf_data.data_pack(cf_dict[cf]["data"])
        cf_data.data_ru_pack(cf_dict[cf]["data_ru"])
        add_to_db.append(cf_data)

    db_session.execute(FamilyCompound.__table__.delete()) # type: ignore
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("[white]ok")


def make_anki_data(cf_dict):
    """Make data list for anki updater."""

    anki_data_list = []
    
    for family in cf_dict:
        anki_family = f"<b>{family}</b>"
        html = "<table><tbody>"
        for row in cf_dict[family]["anki"]:
            headword, pos, meaning, construction = row
            html += "<tr valign='top'>"
            html += "<div style='color: #FFB380'>"
            html += f"<td>{headword}</td>"
            html += f"<td><div style='color: #FF6600'>{pos}</div></td>"
            html += f"<td><div style='color: #FFB380'>{meaning}</td>"
            html += f"<td><div style='color: #FF6600'>{construction}</div></td></tr>"
        html += "</tbody></table>"
        
        if len(html) > 131072:
            print(f"[red]{family} longer than 131072 characters")
        else:
            anki_data_list += [(anki_family, html)]
    
    return anki_data_list


def update_db_cache(db_session, cf_dict):
    """Update the db_info with cf_set for use in the exporter."""
    
    print("[green]adding DbInfo cache item")

    cf_set = set()
    for i in cf_dict:
        cf_set.add(i)
    
    cf_set_cache = db_session \
        .query(DbInfo) \
        .filter_by(key="cf_set") \
        .first()

    if not cf_set_cache:    
        cf_set_cache = DbInfo()
    
    cf_set_cache.key = "cf_set"
    cf_set_cache.value = json.dumps(list(cf_set), ensure_ascii=False, indent=1)
    db_session.add(cf_set_cache)
    db_session.commit()


if __name__ == "__main__":
    main()
