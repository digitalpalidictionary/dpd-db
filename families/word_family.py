#!/usr/bin/env python3.11

"""Create an html list of all words belonging to the same word family."""

from rich import print

from tools.tic_toc import tic, toc
from tools.superscripter import superscripter_uni
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_sort_key
from tools.meaning_construction import degree_of_completion
from db.get_db_session import get_db_session
from db.models import PaliWord, FamilyWord


def main():
    """Runtime."""
    tic()

    print("[bright_yellow]word families generator")

    db_session = get_db_session("dpd.db")

    wf_db = db_session.query(
        PaliWord).filter(PaliWord.family_word != "").all()
    wf_db = sorted(wf_db, key=lambda x: pali_sort_key(x.pali_1))

    wf_dict = make_word_fam_dict(wf_db)
    wf_dict = compile_wf_html(wf_db, wf_dict)
    errors_list = add_wf_to_db(db_session, wf_dict)
    print_errors_list(errors_list)
    toc()


def make_word_fam_dict(wf_db):
    print("[green]extracting word families", end=" ")

    # create a dict of all word families
    # word: {headwords: [], html: "", }

    wf_dict: dict = {}

    for counter, i in enumerate(wf_db):
        wf = i.family_word

        if " " in wf:
            print("[bright_red]ERROR: spaces found please remove!")

        if wf in wf_dict:
            wf_dict[wf]["headwords"] += [i.pali_1]
        else:
            wf_dict[wf] = {
                "headwords": [i.pali_1],
                "html": ""}

    print(len(wf_dict))
    return wf_dict


def compile_wf_html(wf_db, wf_dict):
    print("[green]compiling html")

    for counter, i in enumerate(wf_db):
        wf = i.family_word
        if i.pali_1 in wf_dict[wf]["headwords"]:
            if wf_dict[wf]["html"] == "":
                html_string = "<table class='family'>"
            else:
                html_string = wf_dict[wf]["html"]

            meaning = make_meaning(i)
            html_string += "<tr>"
            html_string += f"<th>{superscripter_uni(i.pali_1)}</th>"
            html_string += f"<td><b>{i.pos}</b></td>"
            html_string += f"<td>{meaning} {degree_of_completion(i)}</td>"
            html_string += "</tr>"

            wf_dict[wf]["html"] = html_string

    for i in wf_dict:
        wf_dict[i]["html"] += "</table>"

    return wf_dict


def add_wf_to_db(db_session, wf_dict):
    print("[green]adding to db", end=" ")

    add_to_db = []
    errors_list = []

    for counter, wf in enumerate(wf_dict):
        if len(wf_dict[wf]["headwords"]) < 2:
            errors_list += [wf]

        wf_data = FamilyWord(
            word_family=wf,
            html=wf_dict[wf]["html"],
            count=len(wf_dict[wf]["headwords"]))
        add_to_db.append(wf_data)

    db_session.execute(FamilyWord.__table__.delete())
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("[white]ok")

    return errors_list


def print_errors_list(errors_list):
    if len(errors_list) > 0:
        print("[bright_red]ERROR: only 1 word in family:", end=" ")
    for error in errors_list:
        print(f"{error}", end=" ")
    print()


if __name__ == "__main__":
    main()
