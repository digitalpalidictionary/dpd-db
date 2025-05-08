#!/usr/bin/env python3

"""Generic find and replace characters in a specific column."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

find_char = " "
replace_char = " "
column = "meaning_1"


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    counter = 0
    for i in db:
        # grab the text from the column
        old_field = getattr(i, column)

        if find_char in old_field:
            new_field = old_field.replace(find_char, replace_char)

            print(f"[white]{i.id}  {i.lemma_1:<40}")
            print(f"[green]{old_field}")
            print(f"[light_green]{new_field}")
            print()
            setattr(i, column, new_field)
            counter += 1

    if counter > 0:
        print("\n[green]would you like to commit changes to db? y/n ", end="")
        route = input()
        if route == "y":
            db_session.commit()
            print("[green]committed to db")
        else:
            print("[green]not committed to db")
    else:
        print("\n[green]nothing found")


if __name__ == "__main__":
    main()
