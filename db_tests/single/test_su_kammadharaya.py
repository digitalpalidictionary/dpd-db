#!/usr/bin/env python3

"""Find all words starting with su and make sure they are kammadhāraka"""

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    i: DpdHeadword
    counter: int = 0

    for i in db:
            if (
                i.construction.startswith("su + ")
                and "kammadhāraya" not in i.compound_type 
            ):
                print(i.lemma_1, i.pos)
                print(i.meaning_combo)
                print(i.construction)
                counter += 1
                pyperclip.copy(i.lemma_1)
                input()
    
    print(counter)



if __name__ == "__main__":
    main()
