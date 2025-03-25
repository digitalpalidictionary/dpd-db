#!/usr/bin/env python3

"""Search bold_definitions using vanilla find or regex."""

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import BoldDefinition
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.title("searching bold definitions")
    bold_definitions_db = fetch_db()
    request_search_terms(bold_definitions_db)


def fetch_db():
    pr.green("fetching bold definitions")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(BoldDefinition).all()
    pr.yes("ok")
    return db


def request_search_terms(db):
    print("[light_green]search for the definition of:[yellow]", end=" ")
    search1 = input()
    print("[light_green]containing:[yellow]", end=" ")
    search2 = input()
    test_regex(search1, search2, db)


def test_regex(search1, search2, db):
    print("[green]test search terms for regex", end=" ")
    regex_characters = ["\\.", "\\/", "\\[", "\\]", "\\(", "\\)", "$", "^"]
    regex_str = "|".join(regex_characters)

    # regex search
    if re.findall(regex_str, search1):
        regex_search(search1, search2, db)

    elif re.findall(regex_str, search2):
        regex_search(search1, search2, db)
    else:
        plain_search(search1, search2, db)


def regex_search(search1, search2, db):
    print("[green]regex search", end=" ")
    search_results = []
    for i in db:
        if re.findall(search1, i.bold) and re.findall(search2, i.commentary):
            search_results.append(i)
    display_results(db, search1, search2, search_results)


def plain_search(search1, search2, db):
    print("[green]plain search", end=" ")
    search_results = []
    for i in db:
        if search1 in i.bold and search2 in i.commentary:
            search_results.append(i)
    display_results(db, search1, search2, search_results)


def display_results(db, search1, search2, search_results):
    counter = 1
    for counter, i in enumerate(search_results):
        print(f"{counter + 1}. [bright_blue]{i.bold}[white]{i.bold_end}")
        commentary = i.commentary.replace(r"<b>", "[cyan]").replace(r"</b>", "[/cyan]")
        if search2:
            search2_results = re.findall(search2, commentary)
            for s2 in search2_results:
                commentary = re.sub(s2, f"[light_green]{s2}[/light_green]", commentary)
        print(f"{commentary}")
        print(f"[green]{i.file_name} {i.nikaya}")
        print(f"[green]{i.book} {i.title} {i.subhead}")
        print()

    print(f"{counter + 1} [green]results displayed")
    request_search_terms(db)


if __name__ == "__main__":
    main()
