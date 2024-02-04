#!/usr/bin/env python3

"""Generic find and replace chacters in a specific column."""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths

find_char = '"'
repalce_char = "'"
column = "non_ia"

def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()
    for i in db:
        old_field = getattr(i, column)
        
        if find_char in old_field:
            new_field = old_field.replace(find_char, repalce_char)
            
            print(f"[green]{old_field}")
            print(f"[light_green]{new_field}")
            setattr(i, column, new_field)

    print("\n[green]would you like to commit changes to db? y/n ", end="")
    route = input()
    if route == "y":
        db_session.commit()
        print("[green]committed to db")
    else:
        print("[green]not committed to db")



if __name__ == "__main__":
    main()

    