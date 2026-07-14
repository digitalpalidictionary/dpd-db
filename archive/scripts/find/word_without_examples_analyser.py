#!/usr/bin/env python3

"""Report headwords with no example_1, bucketed into compound / root / family_word /
unclassified counts."""

import re

from icecream import ic
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main() -> None:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).filter(DpdHeadword.example_1 == "").all()
    compounds = 0
    words = 0
    roots = 0
    huh = 0
    for i in db:
        if re.findall(r"\bcomp\b", i.grammar):
            compounds += 1
        elif i.root_key:
            roots += 1
        elif i.family_word:
            words += 1
        else:
            huh += 1

    ic(compounds)
    ic(roots)
    ic(words)
    ic(huh)
    ic(compounds + roots + words + huh)
    ic(len(db))


if __name__ == "__main__":
    main()
