#!/usr/bin/env python3

"""Find and replace sandhi contractions (imam'eva) 
in example_1, example_2 and commentary."""

import re
import pyperclip

from sqlalchemy import or_
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths

class ProgData():
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.find_me: str
        self.replace_me: str
    
    def refresh_session(self):
        db_session = get_db_session(self.pth.dpd_db_path)
        self.db_session = db_session

    
def main():
    print("[bright_yellow]find and replace sandhi contractions")
    input_word()


def input_word():
    pd = ProgData()

    print("-"*50)
    print()
    print(f"[green]{'word to find':<40}", end="")
    find_me = input()
    if find_me == "x":
        return
    
    pd.find_me = find_me

    print(f"[green]{'word to replace':<40}", end="")
    replace_me = input()
    if replace_me == "x":
        return
    
    pd.replace_me = replace_me
   
    print()
    print(f"[green]replace [cyan]{find_me} [green]with [light_green]{replace_me}?")
    print("[white]y[green]es, [white]n[green]o, search in [white]b[green]old, e[white]x[green]it ", end="")
    route = input()
    print()
    if route == "n":
        input_word()
    elif route == "b":
        find_instances_in_bold(pd)
    elif route == "x":
        return
    else:
        find_instances(pd)


def find_instances(pd):
    db = pd.db_session.query(DpdHeadword) \
        .filter(
            or_(
                DpdHeadword.example_1.contains(pd.find_me),
                DpdHeadword.example_2.contains(pd.find_me),
                DpdHeadword.commentary.contains(pd.find_me))
                ).all()
   
    pd.db = db

    counter = 0
    for i in pd.db:
        for column in ["example_1", "example_2", "commentary"]:
            field = getattr(i, column)
            if field.find(pd.find_me) != -1:
                counter += 1
    
    print(f"{counter} instance(s) found")
    print()

    if counter != 0:
        replace_instances(pd)
    else:
        find_instances_in_bold(pd)


def find_instances_in_bold(pd):
    db = pd.db_session.query(DpdHeadword).all()
    pd.db = db

    print("[green]searching inside bold strings")
    counter = 0

    found_list = []
    for i in pd.db:
        for field in ["example_1", "example_2", "commentary"]:
            clean_field = getattr(i, field) \
                .replace("<b>", "") \
                .replace("</b>", "")
            if clean_field.find(pd.find_me) != -1:
                counter += 1
                found_list += [(i.lemma_1, field)]

    print(f"{counter} instance(s) found")
    print()

    if counter > 0:
        print("[green]replace the following fields manually")
        for i in found_list:
            print(f"[green]{i[0]:<30}[cyan]{i[1]:<20}[white]{pd.find_me}")
    
    db_search = db_search_string([i[0] for i in found_list])
    pyperclip.copy(db_search)
    print()
    print("[green]db search string copied to clipboard")
    print(f"[white]{db_search}")
    print("[green]press any key to continue ", end="")
    input()
    print()

    input_word()
    

def replace_instances(pd):
    counter = 0
    route = None

    for i in pd.db:
        if route == "x":      
            break

        for column in ["example_1", "example_2", "commentary"]:
            field = getattr(i, column)
            if field.find(pd.find_me) != -1:
                counter += 1

                print(f"[green]{counter}. {i.lemma_1}: {column}")
                print()
                
                print("[yellow]before")
                example_before = field.replace(
                    pd.find_me,
                    f"[cyan]{pd.find_me}[/cyan]")
                print(example_before)
                print()
                
                print("[yellow]after")
                example_after = field.replace(
                    pd.find_me,
                    f"[light_green]{pd.replace_me}[/light_green]")
                print(example_after)
                print()

                print("[green]press [white]c[green]ommit or any key to continue ", end="")
                route = input()
                
                if route == "c":
                    setattr(
                        i,
                        column, 
                        re.sub(pd.find_me, pd.replace_me, field)
                    )
                    try:
                        pd.db_session.commit()
                        print(f"[cyan]{pd.find_me}[green] > [light_green]{pd.replace_me} [green]committed to db")
                        print()
                    except Exception as e:
                        print(f"[red]{e}")
                        replace_instances(pd)

                elif route == "x":
                    break
                
    input_word()
            

if __name__ == "__main__":
    main()



# unused
def replace_instances_regex(pd):
    counter = 0
    route = None

    for i in pd.db:
        if route == "x":  
            break

        for column in ["example_1", "example_2", "commentary"]:
            field = getattr(i, column)
            if re.findall(pd.find_me, field):
                counter += 1

                print()
                print(f"[green]{counter}. {i.lemma_1}: {column}")
                print()
                
                print("[yellow]before")
                example_before = re.sub(
                    pd.find_me,
                    f"[cyan]{pd.find_me}[/cyan]",
                    field)
                print(example_before)
                print()
                
                print("[yellow]after")
                example_after = re.sub(
                    pd.find_me,
                    f"[light_green]{pd.replace_me}[/light_green]",
                    field)
                print(example_after)
                print()
                print("[green]press [white]c[green]ommit or any key to continue ", end="")
                route = input()
                print()

                if route == "c":
                    setattr(
                        i,
                        column, 
                        re.sub(pd.find_me, pd.replace_me, field)
                    )
                    pd.db_session.commit()
                    print(f"[cyan]{pd.find_me}[green] > [light_green]{pd.replace_me} [green]committed to db")
                    print()
                
                elif route == "x":
                    break
            
                
    input_word()