#!/usr/bin/env python3.10

import re

from rich import print
from pathlib import Path

from tools.timeis import tic, toc
from tools.superscripter import superscripter_uni
from tools.make_meaning import make_meaning
from db.db_helpers import get_db_session
from db.models import PaliWord, FamilySet


def main():
    tic()
    print("[bright_yellow]sets generator")
    db_path = Path("dpd.db")
    db_session = get_db_session(db_path)

    sets_db = db_session.query(
        PaliWord.family_set).filter(
            PaliWord.family_set != "").order_by(
                PaliWord.pali_1).all()

    print("[green]extracting set names", end=" ")

    sets_set = set()
    exceptions = ["dps", "ncped", "pass1", "sandhi"]

    for row in sets_db:
        words = row[0].split("; ")
        for word in words:
            if word not in exceptions:
                sets_set.add(word)

    print(len(sets_set))

    if " " in sets_set:
        print("[bright_red]ERROR: spaces found please remove!")
    if "" in sets_set:
        print("[bright_red]ERROR: '' found please remove!")
    if "+" in sets_set:
        print("[bright_red]ERROR: + found please remove!")

    add_to_db = []
    length = len(sets_set)
    errors_list = []

    # !!!!!!!!!!!!!!!!!!!!!! pali alphabetical order !!!!!!!!!!!!!!!!!!
    # !!!!!!!!!!!!!!!! or custom alphabetical order !!!!!!!!!!!!!!!!

    for counter, set_name in enumerate(sets_set):

        if counter % 25 == 0:
            print(f"{counter:>9,} / {length:<9,} {set_name}")

        sets_db = db_session.query(PaliWord).filter(
            PaliWord.family_set.contains(set_name)).order_by(
            PaliWord.pali_1).all()

        html_list = ["<table class='table1'>"]
        count = 0

        for i in sets_db:

            test = set_name in i.family_set.split("; ")

            if test:
                count += 1
                meaning = make_meaning(i)

                html_list += [f"<tr><th>{superscripter_uni(i.pali_1)}</th>"]
                html_list += [f"<td><b>{i.pos}</b></td>"]
                html_list += [f"<td>{meaning}</td></tr>"]

        html_list += ["""</table>"""]
        html_string = "".join(html_list)

        st = FamilySet(
            set=set_name,
            html=html_string,
            count=count
        )

        add_to_db.append(st)

        with open(
                f"xxx delete/sets/{set_name}.html", "w") as f:
            f.write(html_string)

        if count < 3:
            errors_list += [set_name]

    if errors_list != []:
        print("[bright_red]ERROR: less than 3 names in set: ")
        for error in errors_list:
            print(f"[red]{error}")

    print("[green]adding to db", end=" ")
    db_session.execute(FamilySet.__table__.delete())
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("[white]ok")

    toc()


if __name__ == "__main__":
    main()
