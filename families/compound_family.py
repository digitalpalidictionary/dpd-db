#!/usr/bin/env python3.11

import re

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord, FamilyCompound
from tools.meaning_construction import clean_construction
from tools.meaning_construction import degree_of_completion
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths as PTH
from tools.superscripter import superscripter_uni
from tools.tic_toc import tic, toc
from tools.tsv_read_write import write_tsv_list
from tools.date_and_time import day


def main():
    tic()
    print("[bright_yellow]compound families generator")

    db_session = get_db_session("dpd.db")

    dpd_db = db_session.query(
        PaliWord).filter(PaliWord.family_compound != "").all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.pali_1))

    cf_dict = create_comp_fam_dict(dpd_db)
    cf_dict = compile_cf_html(dpd_db, cf_dict)
    add_cf_to_db(db_session, cf_dict)
    anki_exporter(cf_dict)
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
                        "html": "",
                        "data": []
                    }

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

                    # anki data
                    if i.meaning_1:
                        construction = clean_construction(
                            i.construction) if i.meaning_1 else ""
                        cf_dict[cf]["data"] += [
                            (i.pali_1, i.pos, meaning, construction)]

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

    db_session.execute(FamilyCompound.__table__.delete())
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("[white]ok")


def anki_exporter(cf_dict):
    """Save to TSV for anki."""
    anki_data_list = []
    for family in cf_dict:
        anki_family = f"<b>{family}</b>"
        html = "<table><tbody>"
        for row in cf_dict[family]["data"]:
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
            anki_data_list += [(anki_family, html, day())]

    file_path = PTH.family_compound_tsv_path
    header = None
    write_tsv_list(file_path, header, anki_data_list)


if __name__ == "__main__":
    main()
