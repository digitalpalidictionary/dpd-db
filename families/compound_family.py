#!/usr/bin/env python3

"""Compile compound familes and save to database."""

import re
from typing import Dict, List, Tuple, TypedDict
from rich import print

from sqlalchemy.orm.session import Session

from db.get_db_session import get_db_session
from db.models import PaliWord, FamilyCompound
from tools.meaning_construction import clean_construction
from tools.meaning_construction import degree_of_completion
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.superscripter import superscripter_uni
from tools.tic_toc import tic, toc
from tools.tsv_read_write import write_tsv_list
from tools.date_and_time import day

class CompoundItem(TypedDict):
    headwords: List[str]
    anki_data: List[Tuple[str, str, str, str]]

CompoundDict = Dict[str, CompoundItem]

def main():
    tic()
    print("[bright_yellow]compound families generator")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db: List[PaliWord] = db_session.query(PaliWord).filter(PaliWord.family_compound != "").all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.pali_1))

    cf_dict: CompoundDict = dict()

    create_comp_fam_dict(dpd_db, cf_dict)
    add_all_cf_to_db(db_session, dpd_db, cf_dict)

    db_session.close()

    anki_exporter(pth, cf_dict)
    toc()


def create_comp_fam_dict(dpd_db: List[PaliWord], cf_dict: CompoundDict) -> None:
    print("[green]extracting compound families and headwords", end=" ")

    # create a dict of all compound families

    for i in dpd_db:
        if i.family_compound is None:
            continue

        for cf in i.family_compound.split(" "):
            if cf == " ":
                print("[bright_red]ERROR: spaces found please remove!")
            elif not cf:
                print("[bright_red]ERROR: '' found please remove!")
            elif cf == "+":
                print("[bright_red]ERROR: + found please remove!")

            test1 = re.findall(r"\bcomp\b", i.grammar) != []
            test2 = "sandhi" in i.pos
            test3 = "idiom" in i.pos
            test4 = len(re.sub(r" \d.*$", "", i.pali_1)) < 30
            test5 = i.meaning_1

            if (test1 or test2 or test3) and test4 and test5:

                if cf in cf_dict:
                    cf_dict[cf]["headwords"] += [i.pali_1]
                else:
                    cf_dict[cf] = CompoundItem(
                        headwords = [i.pali_1],
                        anki_data = [],
                    )

    print(len(cf_dict))

def render_compound_family_html(i: PaliWord) -> str:
    html_string = "<table class='family'>"

    meaning = make_meaning(i)
    html_string += "<tr>"
    html_string += f"<th>{superscripter_uni(i.pali_1)}</th>"
    html_string += f"<td><b>{i.pos}</b></td>"
    html_string += f"<td>{meaning} {degree_of_completion(i)}</td>"
    html_string += "</tr>"

    html_string += "</table>"

    return html_string

def add_anki_data_family_html(i: PaliWord, cf_item: CompoundItem) -> None:
    meaning = make_meaning(i)
    if i.meaning_1:
        construction = clean_construction(
            i.construction) if i.meaning_1 else ""

        cf_item["anki_data"] += [
            (i.pali_1, i.pos, meaning, construction)]


def add_all_cf_to_db(db_session: Session, dpd_db: List[PaliWord], cf_dict: CompoundDict) -> None:
    print("[green]adding to db", end=" ")

    db_session.execute(FamilyCompound.__table__.delete()) # type: ignore

    for i in dpd_db:
        if i.family_compound is None:
            continue

        for cf_key in i.family_compound.split(" "):

            if cf_key in cf_dict.keys():
                cf_item = cf_dict[cf_key]

                fc = db_session.query(FamilyCompound) \
                               .filter(FamilyCompound.compound_family == cf_key) \
                               .first()

                if fc is None:
                    fc = FamilyCompound(
                        compound_family=cf_key,
                        html=render_compound_family_html(i),
                        count=len(cf_item["headwords"]))

                    db_session.add(fc)

                if i.pali_1 in cf_item["headwords"]:
                    if fc not in i.family_compounds:
                        i.family_compounds.append(fc)
                    add_anki_data_family_html(i, cf_item)

    db_session.commit()
    print("[white]ok")

def anki_exporter(pth: ProjectPaths, cf_dict: CompoundDict) -> None:
    """Save to TSV for anki."""
    anki_data_list = []
    for family in cf_dict:
        anki_family = f"<b>{family}</b>"
        html = "<table><tbody>"
        for row in cf_dict[family]["anki_data"]:
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

    file_path = pth.family_compound_tsv_path
    header = []
    write_tsv_list(str(file_path), header, anki_data_list)


if __name__ == "__main__":
    main()
