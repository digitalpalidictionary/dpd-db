#!/usr/bin/env python3

"""Find and replace sandhi contractions (imam'eva)
in example_1, example_2 and commentary."""

import re

import pyperclip
from rich import print
from sqlalchemy import or_

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths


class GlobalVars:
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
    g = GlobalVars()

    print("-" * 50)
    print()
    print(f"[green]{'word to find':<40}", end="")
    find_me = input()
    if find_me == "x":
        return

    g.find_me = find_me

    print(f"[green]{'word to replace':<40}", end="")
    replace_me = input()
    if replace_me == "x":
        return

    g.replace_me = replace_me

    print()
    print(f"[green]replace [cyan]{find_me} [green]with [light_green]{replace_me}?")
    print(
        "[white]y[green]es, [white]n[green]o, search in [white]b[green]old, e[white]x[green]it ",
        end="",
    )
    route = input()
    print()
    if route == "n":
        input_word()
    elif route == "b":
        find_instances_in_bold(g)
    elif route == "x":
        return
    else:
        find_instances(g)


def find_instances(g):
    db = (
        g.db_session.query(DpdHeadword)
        .filter(
            or_(
                DpdHeadword.example_1.contains(g.find_me),
                DpdHeadword.example_2.contains(g.find_me),
                DpdHeadword.commentary.contains(g.find_me),
            )
        )
        .all()
    )

    g.db = db

    counter = 0
    for i in g.db:
        for column in ["example_1", "example_2", "commentary"]:
            field = getattr(i, column)
            if field.find(g.find_me) != -1:
                counter += 1

    print(f"{counter} instance(s) found")
    print()

    if counter != 0:
        replace_instances(g)
    else:
        find_instances_in_bold(g)


def find_instances_in_bold(g):
    db = g.db_session.query(DpdHeadword).all()
    g.db = db

    print("[green]searching inside bold strings")
    counter = 0

    found_list = []
    for i in g.db:
        for field in ["example_1", "example_2", "commentary"]:
            clean_field = getattr(i, field).replace("<b>", "").replace("</b>", "")
            if clean_field.find(g.find_me) != -1:
                counter += 1
                found_list += [(i.lemma_1, field)]

    print(f"{counter} instance(s) found")
    print()

    if counter > 0:
        print("[green]replace the following fields manually")
        for i in found_list:
            print(f"[green]{i[0]:<30}[cyan]{i[1]:<20}[white]{g.find_me}")

    db_search = db_search_string([i[0] for i in found_list])
    pyperclip.copy(db_search)
    print()
    print("[green]db search string copied to clipboard")
    print(f"[white]{db_search}")
    print("[green]press any key to continue ", end="")
    input()
    print()

    input_word()


def replace_instances(g):
    counter = 0
    route = None

    for i in g.db:
        if route == "x":
            break

        for column in ["example_1", "example_2", "commentary"]:
            field = getattr(i, column)
            if field.find(g.find_me) != -1:
                counter += 1

                print(f"[green]{counter}. {i.lemma_1}: {column}")
                print()

                print("[yellow]before")
                example_before = field.replace(g.find_me, f"[cyan]{g.find_me}[/cyan]")
                print(example_before)
                print()

                print("[yellow]after")
                example_after = field.replace(
                    g.find_me, f"[light_green]{g.replace_me}[/light_green]"
                )
                print(example_after)
                print()

                print(
                    "[green]press [white]c[green]ommit or any key to continue ", end=""
                )
                route = input()

                if route == "c":
                    setattr(i, column, re.sub(g.find_me, g.replace_me, field))
                    try:
                        g.db_session.commit()
                        print(
                            f"[cyan]{g.find_me}[green] > [light_green]{g.replace_me} [green]committed to db"
                        )
                        print()
                    except Exception as e:
                        print(f"[red]{e}")
                        replace_instances(g)

                elif route == "x":
                    break

    input_word()


if __name__ == "__main__":
    main()


# unused
def replace_instances_regex(g):
    counter = 0
    route = None

    for i in g.db:
        if route == "x":
            break

        for column in ["example_1", "example_2", "commentary"]:
            field = getattr(i, column)
            if re.findall(g.find_me, field):
                counter += 1

                print()
                print(f"[green]{counter}. {i.lemma_1}: {column}")
                print()

                print("[yellow]before")
                example_before = re.sub(g.find_me, f"[cyan]{g.find_me}[/cyan]", field)
                print(example_before)
                print()

                print("[yellow]after")
                example_after = re.sub(
                    g.find_me, f"[light_green]{g.replace_me}[/light_green]", field
                )
                print(example_after)
                print()
                print(
                    "[green]press [white]c[green]ommit or any key to continue ", end=""
                )
                route = input()
                print()

                if route == "c":
                    setattr(i, column, re.sub(g.find_me, g.replace_me, field))
                    g.db_session.commit()
                    print(
                        f"[cyan]{g.find_me}[green] > [light_green]{g.replace_me} [green]committed to db"
                    )
                    print()

                elif route == "x":
                    break

    input_word()
