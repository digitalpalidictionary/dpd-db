#!/usr/bin/env python3.10

import re
import json

from rich import print
from datetime import date
from pathlib import Path


from tools.timeis import tic, toc
from tools.superscripter import superscripter_uni
from tools.make_meaning import make_meaning
from tools.pali_sort_key import pali_sort_key
from db.db_helpers import get_db_session
from db.models import PaliWord, FamilyWord


def main():
    tic()
    print("[bright_yellow]word families generator")
    db_path = Path("dpd.db")
    db_session = get_db_session(db_path)
    family_word_db = db_session.query(
        PaliWord.family_word
        ).filter(PaliWord.family_word != "").all()

    print("[green]extracting word families", end=" ")
    word_families_set: set = set()
    for row in family_word_db:
        # word_families_set.add
        words = row[0].split(" ")
        for word in words:
            if word == words[-1]:   # ignore prefixes
                word_families_set.add(word)

    print(len(word_families_set))

    if " " in word_families_set:
        print("[bright_red]ERROR: spaces found please remove!")
    if "" in word_families_set:
        print("[bright_red]ERROR: '' found please remove!")

    add_to_db = []
    length = len(word_families_set)
    error_list = []

    for counter, word_family in enumerate(word_families_set):

        word_family_db = db_session.query(PaliWord).filter(
            PaliWord.family_word.regexp_match(fr"\b{word_family}$")
            ).order_by(PaliWord.pali_1).all()

        word_family_db = sorted(
            word_family_db, key=lambda x: pali_sort_key(x.pali_1))

        if len(word_family_db) == 1:
            error_list += word_family

        html_string = "<table class='family'>"

        for i in word_family_db:
            meaning = make_meaning(i)

            html_string += f"<tr><th>{superscripter_uni(i.pali_1)}</th>"
            html_string += f"<td><b>{i.pos}<b></td>"
            html_string += f"<td>{meaning}</td></tr>"""

        html_string += """</table>"""

        wf = FamilyWord(
            word_family=word_family,
            html=html_string,
            count=len(word_family_db)
        )

        add_to_db.append(wf)

        if counter % 100 == 0:
            print(f"{counter:>10,} / {length:<10,} {word_family}")
            with open(f"xxx delete/word_family/{word_family}.html", "w") as f:
                f.write(html_string)

    if len(error_list) > 0:
        print("[bright_red]ERROR: only 1 word in family:", end=" ")
        for error in error_list:
            print(f"{error}", end=" ")
        print()

    print("[green]adding to db", end=" ")
    db_session.execute(FamilyWord().__table__.delete())
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("[white]ok")

    toc()


if __name__ == "__main__":
    main()
