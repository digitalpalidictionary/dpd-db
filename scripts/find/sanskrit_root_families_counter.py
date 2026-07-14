#!/usr/bin/env python3

"""Interactive TUI: count headwords per root_key (only where family_root is set and
sanskrit has no unresolved bracket), list root keys by frequency, and copy each to the
clipboard in turn for manual sanskrit root-family lookup. Press enter to advance, x to quit."""

from collections import Counter

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main() -> None:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    root_family_dict: dict[str, int] = {}
    for i in db:
        if i.root_key and i.family_root and "[" not in i.sanskrit:
            if i.root_key not in root_family_dict:
                root_family_dict[i.root_key] = 1
            else:
                root_family_dict[i.root_key] += 1

    root_family_counter = Counter(root_family_dict)

    # Print the most common values
    for key, count in root_family_counter.most_common():
        print(key, count)
        pyperclip.copy(key)
        route = input()
        if route == "x":
            return


if __name__ == "__main__":
    main()

# upto √ñā 553
