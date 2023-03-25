#!/usr/bin/env python3.11

import re

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord, FamilyCompound
from tools.timeis import tic, toc
from tools.superscripter import superscripter_uni
from tools.make_meaning import make_meaning
from tools.pali_sort_key import pali_sort_key
from tools.degree_of_completion import degree_of_completion


def main():
    """Run it."""
    tic()
    print("[bright_yellow]compound families generator")

    db_session = get_db_session("dpd.db")

    dpd_db = db_session.query(
        PaliWord).filter(PaliWord.family_compound != "").all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.pali_1))

    cf_dict = create_comp_fam_dict(dpd_db)
    cf_dict = compile_cf_html(dpd_db, cf_dict)
    add_cf_to_db(db_session, cf_dict)
    toc()


def create_comp_fam_dict(dpd_db):
    print("[green]extracting compound families and headwords", end=" ")

    # create a dict of all compound families
    # family: {headwords: [], html: "", }

    cf_dict: dict = {}

    for counter, i in enumerate(dpd_db):

        for cf in i.family_compound_list:
            if cf == " ":
                print("[bright_red]ERROR: spaces found please remove!")
            elif cf == "":
                print("[bright_red]ERROR: '' found please remove!")
            elif cf == "+":
                print("[bright_red]ERROR: + found please remove!")

            test1 = re.findall(r"\bcomp\b", i.grammar) != []
            test2 = "sandhi" in i.pos
            test3 = "idiom" in i.pos
            test4 = len(re.sub(r" \d.*$", "", i.pali_1)) < 30
            test5 = i.meaning_1 != ""

            if (test1 or test2 or test3) and test4 and test5:

                if cf in cf_dict:
                    cf_dict[cf]["headwords"] += [i.pali_1]
                else:
                    cf_dict[cf] = {
                        "headwords": [i.pali_1],
                        "html": ""}

    print(len(cf_dict))
    return cf_dict


def compile_cf_html(dpd_db, cf_dict):
    print("[green]compiling html")

    for counter, i in enumerate(dpd_db):

        for cf in i.family_compound_list:
            if cf in cf_dict:
                if i.pali_1 in cf_dict[cf]["headwords"]:
                    if cf_dict[cf]["html"] == "":
                        html_string = "<table class='family'>"
                    else:
                        html_string = cf_dict[cf]["html"]

                    meaning = make_meaning(i)
                    html_string += "<tr>"
                    html_string += f"<th>{superscripter_uni(i.pali_1)}</th>"
                    html_string += f"<td><b>{i.pos}</b></td>"
                    html_string += f"<td>{meaning} {degree_of_completion(i)}</td>"
                    html_string += "</tr>"

                    cf_dict[cf]["html"] = html_string

    for i in cf_dict:
        cf_dict[i]["html"] += "</table>"

    return cf_dict


def add_cf_to_db(db_session, cf_dict):
    print("[green]adding to db", end=" ")

    add_to_db = []

    for counter, cf in enumerate(cf_dict):
        cf_data = FamilyCompound(
            compound_family=cf,
            html=cf_dict[cf]["html"],
            count=len(cf_dict[cf]["headwords"]))
        add_to_db.append(cf_data)

        if counter % 1000 == 0:
            with open(f"xxx delete/compound_family/{cf}.html", "w") as f:
                f.write(cf_dict[cf]["html"])

    db_session.execute(FamilyCompound.__table__.delete())
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("[white]ok")


if __name__ == "__main__":
    main()
