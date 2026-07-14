#!/usr/bin/env python3

"""Pick a random word missing source_1 or example_1, for manual editing in gui2.

Copies each pick's lemma_1 to the clipboard. Press enter for another random
pick, or `x` to quit.
"""

from random import randrange

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    """Loop picking a random word missing source_1 or example_1."""
    pr.yellow_title("pick a random word to add")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    no_source: list[int] = []
    no_example: list[int] = []
    all_missing: list[int] = []

    for i in db:
        if not i.source_1:
            no_source.append(i.id)
        if not i.example_1:
            no_example.append(i.id)

    all_missing.extend(no_example)
    all_missing.extend(no_source)
    print(len(set(all_missing)))

    user_input = ""
    while user_input != "x":
        random_number = randrange(len(all_missing))
        random_id = all_missing[random_number]
        word = db_session.query(DpdHeadword).filter_by(id=random_id).first()
        if word is None:
            continue
        pyperclip.copy(word.lemma_1)
        print(word)
        user_input = input()


if __name__ == "__main__":
    main()
