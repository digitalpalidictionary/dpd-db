#!/usr/bin/env python3

"""Generic find and replace chacters in a specific column."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

from sqlalchemy.orm import joinedload

find_char = ' '
replace_char = " "
column = "meaning_1"

def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs), joinedload(DpdHeadword.ru)).all()
    
    counter = 0
    for i in db:
        # grab the text from the column
        if column.startswith("sbs_"):
            if i.sbs:
                old_field = getattr(i.sbs, column)
            else:
                old_field = ""
        elif column.startswith("ru_"):
            if i.ru:
                old_field = getattr(i.ru, column)
            else:
                old_field = ""
        else:
            old_field = getattr(i, column)
        
        if find_char in old_field:
            new_field = old_field.replace(find_char, replace_char)
            
            print(f"[white]{i.id}  {i.lemma_1:<40}")
            print(f"[green]{old_field}")
            print(f"[light_green]{new_field}")
            print()
            if column.startswith("sbs_"):
                setattr(i.sbs, column, new_field)
            elif column.startswith("ru_"):
                setattr(i.ru, column, new_field)
            else:
                setattr(i, column, new_field)
            counter +=1

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

    