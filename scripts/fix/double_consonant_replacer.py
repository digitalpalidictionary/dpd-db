#!/usr/bin/env python3

"""Find and fix the pattern '-x-x' (hyphen, consonant, hyphen, same consonant)
in example_1, example_2 and commentary columns of dpd_headwords.

Replaces '-x-x' with '-xx' where x is the same Pāḷi consonant.

Run, review the printed matches, then answer y/n to commit.
"""

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

CONSONANTS = "kgcjñṭḍṇṅtdnpbmyrlvshḷ"
PATTERN = re.compile(rf"-([{CONSONANTS}])-\1", re.IGNORECASE)
TAG_PATTERN = re.compile(
    rf"-([{CONSONANTS}])(</?b>)-\1",
    re.IGNORECASE,
)

COLUMNS = ("example_1", "example_2", "commentary")

TAG_ONLY = False


def main() -> None:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    counter = 0
    for i in db:
        for column in COLUMNS:
            old_field: str | None = getattr(i, column)
            if not old_field:
                continue

            new_field, n_tag_subs = TAG_PATTERN.subn(r"-\1\2\1", old_field)
            if TAG_ONLY:
                n_subs = n_tag_subs
            else:
                new_field, n_plain_subs = PATTERN.subn(r"-\1\1", new_field)
                n_subs = n_tag_subs + n_plain_subs
            if n_subs == 0:
                continue

            print(f"[white]{i.id}  {i.lemma_1:<40} [yellow]{column}")
            print(f"[red]{old_field}")
            print(f"[green]{new_field}")
            print()
            setattr(i, column, new_field)
            counter += n_subs

    if counter > 0:
        print(f"\n[cyan]{counter} replacements across {len(COLUMNS)} columns")
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
