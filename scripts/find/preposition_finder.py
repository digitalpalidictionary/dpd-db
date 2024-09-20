#!/usr/bin/env python3

"""Find repeated prepositions in meaning_1."""

import re
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from collections import Counter

def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    total_counter = 0
    for i in db:
        prepositions = re.findall(r"\((.*?)\)", i.meaning_1)
        if (
            prepositions
            and len(prepositions) > 1
        ):
            counter = Counter([prep for prep in prepositions])
            for word, count in counter.items():
                if count > 1:
                    print(f"[cyan]{i.lemma_1} [white]({i.plus_case})")
                    print(f"{i.meaning_1}")
                    print(f"{word}: {count}")
                    print()
                    total_counter +=1
            
    print(total_counter)


if __name__ == "__main__":
    main()
