#!/usr/bin/env python3

"""Compile sets save to database."""

from rich import print

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, FamilySet
from tools.tic_toc import tic, toc
from tools.superscripter import superscripter_uni
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_sort_key
from tools.meaning_construction import degree_of_completion as doc
from tools.paths import ProjectPaths
from tools.configger import config_test

from exporter.ru_components.tools.tools_for_ru_exporter import make_short_ru_meaning, ru_replace_abbreviations, populate_set_ru_and_check_errors
 
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
        sets_db = db_session.query(DpdHeadwords).filter(
            DpdHeadwords.family_set != "").all()
    elif lang == "ru":
        sets_db = db_session.query(DpdHeadwords).options(
            joinedload(DpdHeadwords.ru)).filter(
            DpdHeadwords.family_set != "").all()
    sets_db = sorted(sets_db, key=lambda x: pali_sort_key(x.lemma_1))

    sets_dict = make_sets_dict(sets_db)
    sets_dict = compile_sf_html(sets_db, sets_dict, lang)
    errors_list = add_sf_to_db(db_session, sets_dict)
    print_errors_list(errors_list)
    toc()


def make_sets_dict(sets_db):
    print("[green]extracting set names", end=" ")

    # create a dict of all sets
    # set: {headwords: [], html: "", data:, []}

    sets_dict: dict = {}

    for __counter__, i in enumerate(sets_db):

        for fs in i.family_set_list:
            if fs == " ":
                print("[bright_red]ERROR: spaces found please remove!")
            elif not fs:
                print("[bright_red]ERROR: '' found please remove!")
            elif fs == "+":
                print("[bright_red]ERROR: + found please remove!")

            if i.meaning_1:
                if fs in sets_dict:
                    sets_dict[fs]["headwords"] += [i.lemma_1]
                else:
                    sets_dict[fs] = {
                        "headwords": [i.lemma_1],
                        "html": "",
                        "html_ru": "",
                        "set_ru": "",
                        "data": []}

    print(len(sets_dict))
    return sets_dict


def compile_sf_html(sets_db, sets_dict, lang="en"):
    print("[green]compiling html")

    if lang == "ru":
        populate_set_ru_and_check_errors(sets_dict)

    for __counter__, i in enumerate(sets_db):

        for sf in i.family_set_list:
            if sf in sets_dict:
                if i.lemma_1 in sets_dict[sf]["headwords"]:
                    if not sets_dict[sf]["html"]:
                        html_string = "<table class='family'>"
                    else:
                        html_string = sets_dict[sf]["html"]

                    meaning = make_meaning(i)
                    html_string += "<tr>"
                    html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                    html_string += f"<td><b>{i.pos}</b></td>"
                    html_string += f"<td>{meaning} {doc(i)}</td>"
                    html_string += "</tr>"

                    sets_dict[sf]["html"] = html_string

                    if lang == "ru" and i.ru:
                        if not sets_dict[sf]["html_ru"]:
                            html_string = "<table class='family_ru'>"
                        else:
                            html_string = sets_dict[sf]["html_ru"]

                        ru_meaning = make_short_ru_meaning(i, i.ru)
                        pos = ru_replace_abbreviations(i.pos)
                        html_string += "<tr>"
                        html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                        html_string += f"<td><b>{pos}</b></td>"
                        html_string += f"<td>{ru_meaning} {doc(i)}</td>"
                        html_string += "</tr>"

                        sets_dict[sf]["html_ru"] = html_string

                    # data
                    sets_dict[sf]["data"].append(
                        (i.lemma_1, i.pos, meaning))

    for i in sets_dict:
        sets_dict[i]["html"] += "</table>"
        if lang == "ru":
            sets_dict[i]["html_ru"] += "</table>"

    return sets_dict


def add_sf_to_db(db_session, sets_dict):
    print("[green]adding to db", end=" ")

    add_to_db = []
    errors_list = []

    for __counter__, sf in enumerate(sets_dict):
        count = len(sets_dict[sf]["headwords"])

        sf_data = FamilySet(
            set=sf,
            html=sets_dict[sf]["html"],
            html_ru=sets_dict[sf]["html_ru"],
            set_ru=sets_dict[sf]["set_ru"],
            count=count)
        sf_data.data_pack(sets_dict[sf]["data"])

        add_to_db.append(sf_data)

        if count < 3:
            errors_list += [sf]

    db_session.execute(FamilySet.__table__.delete()) # type: ignore
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("[white]ok")

    return errors_list


def print_errors_list(errors_list):
    if errors_list != []:
        print("[bright_red]ERROR: less than 3 names in set: ")
        for error in errors_list:
            print(f"[red]{error}")


if __name__ == "__main__":
    print("[bright_yellow]sets generator")
    if (
        config_test("exporter", "make_dpd", "yes") or 
        config_test("regenerate", "db_rebuild", "yes") or 
        config_test("exporter", "make_tpr", "yes") or 
        config_test("exporter", "make_ebook", "yes")
    ):
        main()
    else:
        print("generating is disabled in the config")