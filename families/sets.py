#!/usr/bin/env python3

"""Compile sets save to database."""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord, FamilySet
from tools.tic_toc import tic, toc
from tools.superscripter import superscripter_uni
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_sort_key
from tools.meaning_construction import degree_of_completion as doc


def main():
    tic()
    print("[bright_yellow]sets generator")
    db_session = get_db_session("dpd.db")

    sets_db = db_session.query(
        PaliWord).filter(PaliWord.family_set != "").all()
    sets_db = sorted(sets_db, key=lambda x: pali_sort_key(x.pali_1))

    sets_dict = make_sets_dict(sets_db)
    sets_dict = compile_sf_html(sets_db, sets_dict)
    errors_list = add_sf_to_db(db_session, sets_dict)
    print_errors_list(errors_list)
    toc()


def make_sets_dict(sets_db):
    print("[green]extracting set names", end=" ")

    # create a dict of all sets
    # set: {headwords: [], html: "", }

    sets_dict: dict = {}

    for counter, i in enumerate(sets_db):

        for fs in i.family_set_list:
            if fs == " ":
                print("[bright_red]ERROR: spaces found please remove!")
            elif fs == "":
                print("[bright_red]ERROR: '' found please remove!")
            elif fs == "+":
                print("[bright_red]ERROR: + found please remove!")

            if i.meaning_1:
                if fs in sets_dict:
                    sets_dict[fs]["headwords"] += [i.pali_1]
                else:
                    sets_dict[fs] = {
                        "headwords": [i.pali_1],
                        "html": ""}

    print(len(sets_dict))
    return sets_dict


def compile_sf_html(sets_db, sets_dict):
    print("[green]compiling html")

    for counter, i in enumerate(sets_db):

        for sf in i.family_set_list:
            if sf in sets_dict:
                if i.pali_1 in sets_dict[sf]["headwords"]:
                    if sets_dict[sf]["html"] == "":
                        html_string = "<table class='family'>"
                    else:
                        html_string = sets_dict[sf]["html"]

                    meaning = make_meaning(i)
                    html_string += "<tr>"
                    html_string += f"<th>{superscripter_uni(i.pali_1)}</th>"
                    html_string += f"<td><b>{i.pos}</b></td>"
                    html_string += f"<td>{meaning} {doc(i)}</td>"
                    html_string += "</tr>"

                    sets_dict[sf]["html"] = html_string

    for i in sets_dict:
        sets_dict[i]["html"] += "</table>"

    return sets_dict


def add_sf_to_db(db_session, sets_dict):
    print("[green]adding to db", end=" ")

    add_to_db = []
    errors_list = []

    for counter, sf in enumerate(sets_dict):
        count = len(sets_dict[sf]["headwords"])

        sf_data = FamilySet(
            set=sf,
            html=sets_dict[sf]["html"],
            count=count)

        add_to_db.append(sf_data)

        if count < 3:
            errors_list += [sf]

    db_session.execute(FamilySet.__table__.delete())
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
    main()
