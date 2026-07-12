#!/usr/bin/env python3

"""Fill in the missing details of auto-added monks' names in Theragāthā"""

import json

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.goldendict_tools import open_in_goldendict
from tools.paths import ProjectPaths


def main() -> None:
    """Walk the Theragāthā monk-name id range and track review progress."""
    print("[bright_yellow]fill details of theragāthā monks")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    # load previous set or start a new one
    try:
        done_list = load_done_list(pth)
    except FileNotFoundError:
        done_list = []

    first = 76179
    last = 76417
    total = last - first + 1

    print_done(done_list)

    for counter, i in enumerate(db):
        if first <= i.id <= last and i.id not in done_list:
            pyperclip.copy(str(i.id))
            open_in_goldendict(i.lemma_clean)

            processed = len(done_list)
            print(f"{processed + 1:>3}/{total:<3} [green]{counter:<6}{i.lemma_1}")
            print("[yellow]q[white]uit or Enter to continue: ", end="")
            choice = input()

            if choice == "q":
                break
            else:
                done_list += [i.id]

    print_done(done_list)
    save_done_list(pth, done_list)


def load_done_list(pth: ProjectPaths) -> list[int]:
    """Load the list of already-reviewed headword ids."""
    with open(pth.theragatha_filler_path, encoding="utf-8") as f:
        return json.load(f)


def save_done_list(pth: ProjectPaths, done_list: list[int]) -> None:
    """Save the list of already-reviewed headword ids."""
    with open(pth.theragatha_filler_path, "w", encoding="utf-8") as f:
        json.dump(done_list, f, indent=2)


def print_done(done_list: list[int]) -> None:
    """Print how many ids have been reviewed so far."""
    print(f"completed: {len(done_list)}")


if __name__ == "__main__":
    main()
