#!/usr/bin/env python3.10

import re

from rich import print
from pathlib import Path

from tools.timeis import tic, toc
from tools.superscripter import superscripter_uni
from tools.make_meaning import make_meaning
from tools.pali_sort_key import pali_sort_key
from db.db_helpers import get_db_session
from db.models import PaliWord, FamilyCompound


def main():
    tic()
    print("[bright_yellow]compound families generator")
    db_path = Path("dpd.db")
    db_session = get_db_session(db_path)

    compound_family_db = db_session.query(
        PaliWord.family_compound
        ).filter(
            PaliWord.family_compound != "",
            PaliWord.meaning_1 != ""
        ).order_by(
                PaliWord.pali_1
        ).all()

    print("[green]extracting compound families", end=" ")
    compound_families_set: set = set()
    compound_families_clean_set: set = set()
    for row in compound_family_db:
        words = row[0].split(" ")
        for word in words:
            compound_families_set.add(word)
            word_clean = re.sub(r" \d.*$", "", word)
            compound_families_clean_set.add(word_clean)

    print(len(compound_families_set))

    if " " in compound_families_set:
        print("[bright_red]ERROR: spaces found please remove!")
    if "" in compound_families_set:
        print("[bright_red]ERROR: '' found please remove!")
    if "+" in compound_families_set:
        print("[bright_red]ERROR: + found please remove!")

    add_to_db = []
    length = len(compound_families_set)

    for counter, compound_family in enumerate(compound_families_set):

        compound_family_db = db_session.query(
            PaliWord
            ).filter(
                PaliWord.family_compound.contains(compound_family),
                PaliWord.meaning_1 != ""
            ).order_by(
                PaliWord.pali_1
            ).all()

        compound_family_db = sorted(
            compound_family_db, key=lambda x: pali_sort_key(x.pali_1))

        html_list = ["<table class='family'>"]

        cf_count = 0
        for i in compound_family_db:

            test2 = compound_family in i.family_compound.split(" ")
            test3 = len(re.sub(r" \d.*$", "", i.pali_1)) < 30

            if test2 & test3:
                cf_count += 1
                meaning = make_meaning(i)

                html_list += [f"<tr><th>{superscripter_uni(i.pali_1)}</th>"]
                html_list += [f"<td><b>{i.pos}</b></td>"]
                html_list += [f"<td>{meaning}</td></tr>"]

        html_list += ["""</table>"""]
        html_string = "".join(html_list)

        cf = FamilyCompound(
            compound_family=compound_family,
            html=html_string,
            count=cf_count
        )

        add_to_db.append(cf)

        if counter % 500 == 0:
            print(f"{counter:>10,} / {length:<10,} {compound_family}")
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
