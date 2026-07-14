#!/usr/bin/env python3

"""Collapse repeated identical bracketed annotations in meaning_1, e.g.
`(of a bird) goes (to); travels (to)` -> `(of a bird) goes; travels (to)`.

Run, review the printed matches, then answer y/n to commit."""

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def test_brackets_list(brackets_list: list[str]) -> bool:
    """True if every bracketed group after the first is identical to the first."""
    first_word = ""
    for count, word in enumerate(brackets_list):
        if count == 0:
            first_word = word
            continue
        if word == first_word:
            continue
        else:
            return False
    return True


def make_brackets_list(i: DpdHeadword) -> list[str]:
    """Return every bracketed group in meaning_1, ignoring a leading one."""
    meaning_clean = re.sub(r"\(.+?\) ", "", i.meaning_1)
    brackets_list = re.findall(r"\(.*?\)", meaning_clean)
    return brackets_list


def process_brackets(i: DpdHeadword, brackets_list: list[str]) -> None:
    """Remove every repeat occurrence of the first bracketed group."""
    find = re.escape(brackets_list[0])
    subs = len(brackets_list) - 1
    i.meaning_1 = re.sub(
        f" {find}",
        "",
        i.meaning_1,
        subs,
    )


def main() -> None:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    found_count = 0
    for i in db:
        if "(" in i.meaning_1:
            brackets_list = make_brackets_list(i)

            if len(brackets_list) > 1 and test_brackets_list(brackets_list):
                found_count += 1
                print(f"[white]{found_count}")
                print(f"[red]{i.meaning_1}")
                print(brackets_list)

                process_brackets(i, brackets_list)

                print(f"[green]{i.meaning_1}")
                print()

    if found_count > 0:
        print(f"\n[cyan]{found_count} entries with repeated brackets")
        print("[green]would you like to commit changes to db? y/n ", end="")
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
