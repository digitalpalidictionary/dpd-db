#!/usr/bin/env python3.11

import re

from rich import print
from pathlib import Path

from tools.timeis import tic, toc
from tools.superscripter import superscripter_uni
from tools.make_meaning import make_meaning
from tools.pali_sort_key import pali_sort_key
from db.get_db_session import get_db_session
from db.models import PaliWord, FamilySet


def main():
    tic()
    print("[bright_yellow]sets generator")
    db_path = Path("dpd.db")
    db_session = get_db_session(db_path)

    sets_db = db_session.query(
        PaliWord.family_set
        ).filter(
            PaliWord.family_set != "",
            PaliWord.meaning_1 != ""
        ).order_by(
            PaliWord.pali_1
        ).all()

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

    # !!! or custom alphabetical order

    for counter, set_name in enumerate(sets_set):

        sets_db = db_session.query(
            PaliWord
            ).filter(
                PaliWord.family_set.contains(set_name),
                PaliWord.meaning_1 != ""
            ).order_by(
                PaliWord.pali_1
            ).all()

        sets_db = sorted(sets_db, key=lambda x: pali_sort_key(x.pali_1))

        html_list = ["<table class='family'>"]
        count = 0

        for i in sets_db:

            test1 = set_name in i.family_set.split("; ")
            test2 = i.meaning_1 != ""

            if test1 & test2:
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

        if counter % 25 == 0:
            print(f"{counter:>10,} / {length:<10,} {set_name}")
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
