#!/usr/bin/env python3

"""Compile sets save to database."""

from typing import Dict, List, Set, TypedDict
from rich import print

from sqlalchemy.orm.session import Session

from db.get_db_session import get_db_session
from db.models import PaliWord, FamilySet
from tools.tic_toc import tic, toc
from tools.superscripter import superscripter_uni
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_sort_key
from tools.meaning_construction import degree_of_completion as doc
from tools.paths import ProjectPaths

class SetItem(TypedDict):
    headwords: List[str]

SetsDict = Dict[str, SetItem]

def main():
    tic()
    print("[bright_yellow]sets generator")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    sets_db = db_session.query(
        PaliWord).filter(PaliWord.family_set != "").all()
    sets_db = sorted(sets_db, key=lambda x: pali_sort_key(x.pali_1))

    sets_dict: SetsDict = dict()

    make_sets_dict(sets_db, sets_dict)
    errors_list = add_all_sf_to_db(db_session, sets_db, sets_dict)
    print_errors_list(errors_list)

    db_session.close()

    toc()


def make_sets_dict(sets_db: List[PaliWord], sets_dict: SetsDict) -> None:
    print("[green]extracting set names", end=" ")

    # create a dict of all sets

    for i in sets_db:

        for fs in i.family_set_key_list:
            if fs == " ":
                print("[bright_red]ERROR: spaces found please remove!")
            elif not fs:
                print("[bright_red]ERROR: '' found please remove!")
            elif fs == "+":
                print("[bright_red]ERROR: + found please remove!")

            if i.meaning_1:
                if fs in sets_dict:
                    sets_dict[fs]["headwords"] += [i.pali_1]
                else:
                    sets_dict[fs] = SetItem(headwords = [i.pali_1])

    print(len(sets_dict))

def render_sf_html(i: PaliWord) -> str:
    html_string = "<table class='family'>"

    meaning = make_meaning(i)
    html_string += "<tr>"
    html_string += f"<th>{superscripter_uni(i.pali_1)}</th>"
    html_string += f"<td><b>{i.pos}</b></td>"
    html_string += f"<td>{meaning} {doc(i)}</td>"
    html_string += "</tr>"

    html_string += "</table>"

    return html_string

def add_all_sf_to_db(db_session: Session, dpd_db: List[PaliWord], sets_dict: SetsDict) -> List[str]:
    print("[green]adding to db", end=" ")

    db_session.execute(FamilySet.__table__.delete()) # type: ignore

    errors_list = []

    sf_exists: Set[str] = set()
    # First, create all family sets from the semicolon-separated str list in Pali words.
    for i in dpd_db:
        if i.family_set is None:
            continue

        for sf_key in i.family_set.split("; "):
            if sf_key in sets_dict.keys():
                if sf_key in sf_exists:
                    continue
                sf_exists.add(sf_key)

                sf_item = sets_dict[sf_key]
                count = len(sf_item["headwords"])

                fs = FamilySet(
                    set=sf_key,
                    html=render_sf_html(i),
                    count=count)

                db_session.add(fs)

    db_session.commit()

    # Create the associations.

    for i in dpd_db:
        if i.family_set is None:
            continue

        for sf_key in i.family_set.split("; "):

            if sf_key in sets_dict.keys():
                sf_item = sets_dict[sf_key]

                count = len(sf_item["headwords"])

                fs = db_session.query(FamilySet) \
                               .filter(FamilySet.set == sf_key) \
                               .first()

                if fs is None:
                    raise Exception(f"FamilySet {sf_key} not found in db")

                if i.pali_1 in sf_item["headwords"]:
                    if fs not in i.family_sets:
                        i.family_sets.append(fs)

                    if count < 3:
                        errors_list += [sf_key]

    db_session.commit()

    print("[white]ok")

    return errors_list


def print_errors_list(errors_list):
    if errors_list != []:
        print("[bright_red]ERROR: less than 3 names in set: ")
        for error in errors_list:
            print(f"[red]{error}")


if __name__ == "__main__":
    main()
