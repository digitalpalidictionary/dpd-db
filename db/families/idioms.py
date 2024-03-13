#!/usr/bin/env python3

"""Compile idioms and save to database."""

import json
import re

from rich import print

from db.get_db_session import get_db_session
from db.models import DbInfo, DpdHeadwords, FamilyIdiom

from tools.configger import config_test
from tools.meaning_construction import degree_of_completion
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.superscripter import superscripter_uni
from tools.tic_toc import tic, toc

from exporter.ru_components.tools.tools_for_ru_exporter import make_short_ru_meaning, ru_replace_abbreviations

from sqlalchemy.orm import joinedload


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    if config_test("exporter", "language", "en"):
        lang = "en"
    elif config_test("exporter", "language", "ru"):
        lang = "ru"
    # add another lang here "elif ..." and 
    # add conditions if lang = "{your_language}" in every instance in the code.

    if lang == "en":
        dpd_db = db_session.query(
            DpdHeadwords).filter(DpdHeadwords.family_idioms != "").all()
    elif lang == "ru":
        dpd_db = db_session.query(
            DpdHeadwords).options(joinedload(DpdHeadwords.ru)
            ).filter(DpdHeadwords.family_idioms != "").all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    sync_idiom_numbers_with_family_compound(db_session)
    idioms_dict = create_idioms_dict(dpd_db)
    idioms_dict = compile_idioms_html(dpd_db, idioms_dict, lang)
    add_idioms_to_db(db_session, idioms_dict)
    update_db_cache(db_session, idioms_dict)


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
    dpd_db: list[DpdHeadwords] = db_session.query(DpdHeadwords).all()

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
                        "count": 0
                    }

    print(len(idioms_dict))
    return idioms_dict


def compile_idioms_html(dpd_db, idioms_dict, lang="en"):
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

                    meaning = make_meaning(i)
                    html_string += "<tr>"
                    html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                    html_string += f"<td><b>{i.pos}</b></td>"
                    html_string += f"<td>{meaning} {degree_of_completion(i)}</td>"
                    html_string += "</tr>"

                    idioms_dict[word]["html"] = html_string

                    if lang == "ru" and i.ru:
                        if not idioms_dict[word]["html_ru"]:
                            html_string = "<table class='family_ru'>"
                        else:
                            html_string = idioms_dict[word]["html_ru"]

                        ru_meaning = make_short_ru_meaning(i, i.ru)
                        pos = ru_replace_abbreviations(i.pos)
                        html_string += "<tr>"
                        html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                        html_string += f"<td><b>{pos}</b></td>"
                        html_string += f"<td>{ru_meaning} {degree_of_completion(i)}</td>"
                        html_string += "</tr>"

                        idioms_dict[word]["html_ru"] = html_string

                    # data
                    idioms_dict[word]["data"].append(
                    (i.lemma_1, i.pos, meaning))

                    # count
                    idioms_dict[word]["count"] += 1

    for i in idioms_dict:
        idioms_dict[i]["html"] += "</table>"
        if lang == "ru":
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
    tic()
    print("[bright_yellow]idioms generator")

    if (
        config_test("exporter", "make_dpd", "yes") or 
        config_test("regenerate", "db_rebuild", "yes") or 
        config_test("exporter", "make_tpr", "yes") or 
        config_test("exporter", "make_ebook", "yes")
    ):
        main()
    else:
        print("generating is disabled in the config")
    
    toc()
