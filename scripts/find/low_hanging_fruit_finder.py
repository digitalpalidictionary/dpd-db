#!/usr/bin/env python3

"""Interactive TUI: step through words that have an example but no meaning_1,
copying each lemma_1 to the clipboard in turn for manual triage in gui2.
Press enter to advance, or q to quit early."""

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.yellow_title("low hanging fruit finder")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db_results = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.meaning_1 == "")
        .filter(DpdHeadword.example_1 != "")
        .all()
    )
    total = len(db_results)
    print(f"{total} words with example and no meaning 1")
    print("press [blue]enter[/blue] to continue or [blue]q[/blue] to quit")

    for i in db_results:
        print(f"{total} {i.lemma_1}", end=" ")
        pyperclip.copy(i.lemma_1)
        user_input = input()
        if user_input == "q":
            break
        else:
            total -= 1


if __name__ == "__main__":
    main()
