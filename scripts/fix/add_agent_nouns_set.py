#!/usr/bin/env python3

"""One-off migration: add the `agent nouns` family_set to masc agent nouns.

Selects every headword with pos `masc`, a filled `meaning_1` and the word
`agent` in `grammar` — the same match as the db_test
"family_set: masc agent no agent nouns" — and adds `agent nouns` to its
`family_set`. Existing sets are kept and the list is re-sorted into the
same English alphabetical order the gui "Add Set" dropdown uses.

Shows a diff for every changed row and asks for confirmation before
committing.

CLOSE gui2 BEFORE RUNNING — it writes to the same database.

    uv run scripts/fix/add_agent_nouns_set.py
"""

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from scripts.fix.sort_family_sets import sort_family_set
from tools.paths import ProjectPaths
from tools.printer import printer as pr

SET_NAME = "agent nouns"


def add_set(family_set: str, set_name: str) -> str:
    """Add `set_name` to a "; "-separated family_set, keeping existing sets."""
    parts = [part.strip() for part in family_set.split(";")]
    if set_name in parts:
        return family_set
    return sort_family_set(f"{family_set}; {set_name}")


def main() -> None:
    """Add the agent nouns family_set to masc agent nouns in dpd_headwords."""
    pr.yellow_title(f"add '{SET_NAME}' family_set to masc agent nouns")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.pos == "masc", DpdHeadword.meaning_1 != "")
        .all()
    )

    counter = 0
    for i in db:
        if not re.search(r"\bagent\b", i.grammar):
            continue
        old_field = i.family_set
        new_field = add_set(old_field, SET_NAME)

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
        print(f"\n[green]nothing to do — all masc agent nouns already in '{SET_NAME}'")


if __name__ == "__main__":
    main()
