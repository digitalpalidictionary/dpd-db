#!/usr/bin/env python3.10

import re
import json

from rich import print
from datetime import date
from pathlib import Path


from tools.timeis import tic, toc
from tools.superscripter import superscripter_uni
from tools.make_meaning import make_meaning
from db.db_helpers import get_db_session
from db.models import PaliWord, FamilyCompound


def main():
    tic()
    print("[bright_yellow]compound families generator")
    db_path = Path("dpd.db")
    db_session = get_db_session(db_path)

    compound_family_db = db_session.query(
        PaliWord.family_compound).filter(
            PaliWord.family_compound != "",
            PaliWord.meaning_1 != "").order_by(
                PaliWord.pali_1
            ).all()

    print("[green]extracting compound families", end=" ")
    compound_families_set: set = set()
    for row in compound_family_db:
        words = row[0].split(" ")
        for word in words:
            compound_families_set.add(word)

    print(len(compound_families_set))

    if " " in compound_families_set:
        print("[bright_red]ERROR: spaces found please remove!")
    if "" in compound_families_set:
        print("[bright_red]ERROR: '' found please remove!")
    if "+" in compound_families_set:
        print("[bright_red]ERROR: + found please remove!")

    add_to_db = []
    length = len(compound_families_set)

    # !!!!!!!!!!!!!!!!!!!!!! pali alphabetical order !!!!!!!!!!!!!!!!!!

    for x in enumerate(compound_families_set):
        counter = x[0]
        compound_family = x[1]

        if counter % 500 == 0:
            print(f"{counter:>9,} / {length:<9,} {compound_family}")

        compound_family_db = db_session.query(PaliWord).filter(
            PaliWord.family_compound.contains(compound_family),
            PaliWord.meaning_1 != "").order_by(
            PaliWord.pali_1).all()

        html_list = ["<table class='table_family'>"]

        for i in compound_family_db:
            count = 0

            # test1 comp in grammar
            # test2 comp family in the string
            # test3 no root
            # test4 length of p1 without a number is less than 30

            test1 = re.findall(
                r"\bcomp\b", i.grammar) != []
            test2 = compound_family in i.family_compound.split(" ")
            test3 = i.root_key == ""
            test4 = len(re.sub(r" \d.*$", "", i.pali_1)) < 30

            if test1 & test2 & test3 & test4:
                count += 1
                meaning = make_meaning(i)

                html_list += [f"<tr><th>{superscripter_uni(i.pali_1)}</th>"]
                html_list += [f"<td><b>{i.pos}</b></td>"]
                html_list += [f"<td>{meaning}</td></tr>"]

        html_list += ["""</table>"""]
        html_string = "".join(html_list)

        cf = FamilyCompound(
            compound_family=compound_family,
            html=html_string,
            count=count
        )

        add_to_db.append(cf)

        with open(
                f"xxx delete/compound_family/{compound_family}.html", "w") as f:
            f.write(html_string)

    print("[green]adding to db", end=" ")
    db_session.execute(FamilyCompound.__table__.delete())
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("[white]ok")

    toc()


if __name__ == "__main__":
    main()
