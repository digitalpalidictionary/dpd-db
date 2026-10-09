#!/usr/bin/env python3

"""One-off migration: sort `family_set` lists into English alphabetical order.

`family_set` holds a "; "-separated list of set names. When the gui adds a
set via the "Add Set" dropdown, it has historically joined the list in
Pāḷi alphabetical order (`pali_sort_key`) instead of English alphabetical
order — so rows read e.g. "vaggas of Aṅguttara Nikāya 1; suttas of the
Dīgha Nikāya" (v < s in the Pāḷi alphabet) where English order wants the
reverse.

This script rewrites every multi-set `family_set` into case-insensitive
English alphabetical order, showing a diff for every changed row and asking
for confirmation before committing.

CLOSE gui2 BEFORE RUNNING — it writes to the same database.

    uv run scripts/fix/sort_family_sets.py
"""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def english_sort_key(s: str) -> str:
    """Case-insensitive English alphabetical key."""
    return s.lower()


def sort_family_set(value: str) -> str:
    """Sort a "; "-separated family_set list into English alphabetical order."""
    parts = [part.strip() for part in value.split(";") if part.strip()]
    return "; ".join(sorted(parts, key=english_sort_key))


def main() -> None:
    """Sort family_set lists in dpd_headwords into English alphabetical order."""
    pr.yellow_title("sort family_sets into english abc order")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).filter(DpdHeadword.family_set.like("%;%")).all()

    counter = 0
    for i in db:
        old_field = i.family_set
        new_field = sort_family_set(old_field)

        if new_field != old_field:
            counter += 1
            i.family_set = new_field
            print(f"[green]{counter}.")
            print(f"[white]{i.id} {i.lemma_1:<40}")
            print(f"[red]{old_field}")
            print(f"[green]{new_field}")
            print()

    if counter > 0:
        print(f"[amber]{counter} rows to update")
        print("\n[green]would you like to commit changes to db? y/n ", end="")
        route = input()
        if route == "y":
            db_session.commit()
            print("[green]committed to db")
        else:
            print("[green]not committed to db")
    else:
        print("\n[green]nothing to do — all family_sets already in order")


if __name__ == "__main__":
    main()
