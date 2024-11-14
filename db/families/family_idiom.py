#!/usr/bin/env python3

"""Compile idioms and save to database."""

import json
import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DbInfo, DpdHeadword, FamilyIdiom

from tools.configger import config_test
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
    print("[bright_yellow]idioms generator")

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
        .filter(DpdHeadword.family_idioms != "") \
        .all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    sync_idiom_numbers_with_family_compound(db_session)
    idioms_dict = create_idioms_dict(dpd_db)
    idioms_dict = compile_idioms_html(dpd_db, idioms_dict)
    add_idioms_to_db(db_session, idioms_dict)
    update_db_cache(db_session, idioms_dict)
    
    toc()


def sync_idiom_numbers_with_family_compound(db_session):
    """
    Sync idioms with family compound.
    If a family compound has
    - a number
    - no space
    - pos not a compound or sandhi
    - gram does not contain "comp"
    then copy that value to idioms.
    """
    print("[green]syncing idiom numbers with family compound", end=" ")
    dpd_db: list[DpdHeadword] = db_session.query(DpdHeadword).all()

    count = 0
    for i in dpd_db:
        if (
            i.family_compound
            and re.findall("\\d", i.family_compound)
            and " " not in i.family_compound
            and "idioms" not in i.pos
            and "sandhi" not in i.pos
            and not re.findall("\\bcomp\\b", i.grammar)
            and not i.family_idioms
        ):
            i.family_idioms = i.family_compound
            count += 1
    
    db_session.commit()
    print(count)


def create_idioms_dict(dpd_db):
    print("[green]extracting idioms and headwords", end=" ")

    # create a dict of all idioms
    # word: {headwords: [], html: "", data: []}

    idioms_dict: dict = {}
    for i in dpd_db:
        for word in i.family_idioms_list:
            if i.meaning_1:
                if word in idioms_dict:
                    idioms_dict[word]["headwords"].append(i.lemma_1)
                else:
                    idioms_dict[word] = {
                        "headwords": [i.lemma_1],
                        "html": "",
                        "html_ru": "",
                        "data": [],
                        "data_ru": [],
                        "count": 0
                    }

    print(len(idioms_dict))
    return idioms_dict


def compile_idioms_html(dpd_db, idioms_dict):
    print("[green]compiling html")

    for i in dpd_db:
        if i.pos in ["idiom", "sandhi"]:
            for word in i.family_idioms_list:
                if (
                    i.meaning_1
                    and word in idioms_dict
                    and i.lemma_1 in idioms_dict[word]["headwords"]
                ):
                    if not idioms_dict[word]["html"]:
                        html_string = "<table class='family'>"
                    else:
                        html_string = idioms_dict[word]["html"]

                    meaning = make_meaning_combo(i)

                    html_string += "<tr>"
                    html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                    html_string += f"<td><b>{i.pos}</b></td>"
                    html_string += f"<td>{meaning}</td>"
                    html_string += f"<td>{degree_of_completion(i)}</td>"
                    html_string += "</tr>"

                    idioms_dict[word]["html"] = html_string

                    # rus
                    if not idioms_dict[word]["html_ru"]:
                        ru_html_string = "<table class='family'>"
                    else:
                        ru_html_string = idioms_dict[word]["html_ru"]

                    ru_meaning = make_short_ru_meaning(i, i.ru)
                    pos = ru_replace_abbreviations(i.pos)
                    ru_html_string += "<tr>"
                    ru_html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                    ru_html_string += f"<td><b>{pos}</b></td>"
                    ru_html_string += f"<td>{ru_meaning}</td>"
                    ru_html_string += f"<td>{degree_of_completion(i)}</td>"
                    ru_html_string += "</tr>"

                    idioms_dict[word]["html_ru"] = ru_html_string

                    # data
                    idioms_dict[word]["data"].append((
                        i.lemma_1,
                        i.pos,
                        meaning,
                        degree_of_completion(i, html=False)
                    ))

                    # rus data
                    idioms_dict[word]["data_ru"].append((
                        i.lemma_1,
                        pos,
                        ru_meaning,
                        degree_of_completion(i, html=False)
                    ))


                    # count
                    idioms_dict[word]["count"] += 1

    for i in idioms_dict:
        idioms_dict[i]["html"] += "</table>"
        idioms_dict[i]["html_ru"] += "</table>" 

    return idioms_dict


def add_idioms_to_db(db_session, idioms_dict):
    print("[green]adding to db", end=" ")

    add_to_db = []

    for idiom, data in idioms_dict.items():
        if idioms_dict[idiom]["data"]:
            idiom_data = FamilyIdiom(
                idiom=idiom,
                html=idioms_dict[idiom]["html"],
                html_ru=idioms_dict[idiom]["html_ru"],
                count=idioms_dict[idiom]["count"])
            idiom_data.data_pack(idioms_dict[idiom]["data"])
            idiom_data.data_ru_pack(idioms_dict[idiom]["data_ru"])
            add_to_db.append(idiom_data)

    db_session.execute(FamilyIdiom.__table__.delete()) # type: ignore
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("[white]ok")


def update_db_cache(db_session, idioms_dict):
    """Update the db_info with cf_set for use in the exporter."""
    
    print("[green]adding dbinfo cache item")

    idioms_set = set()
    for word in idioms_dict:
        if idioms_dict[word]["count"] > 0:
            idioms_set.add(word)

    idioms_set_cache = db_session \
        .query(DbInfo) \
        .filter_by(key="idioms_set") \
        .first()

    if not idioms_set_cache:    
        idioms_set_cache = DbInfo()
    
    idioms_set_cache.key = "idioms_set"
    idioms_set_cache.value = json.dumps(list(idioms_set), ensure_ascii=False, indent=1)
    db_session.add(idioms_set_cache)
    db_session.commit()


if __name__ == "__main__":
    main()
