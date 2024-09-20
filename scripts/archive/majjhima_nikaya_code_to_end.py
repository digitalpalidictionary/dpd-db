#!/usr/bin/env python3

"""
Move the sutta code to the end of the meaning. 
old: Majjhima Nikāya 24 (MN24); Discourse on the Relay Chariots
new: Majjhima Nikāya 24; Discourse on the Relay Chariots (MN24)
"""

import re
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    for counter, i in enumerate(db):
        if (
            "suttas of the Majjhima Nikāya" in i.family_set
            and i.meaning_1        
        ):
            try:
                meaning_original = f"{i.meaning_1}"
                search_pattern = re.compile(r" \(MN(\d+)\)")
                meaning_modified = re.sub(search_pattern, "", i.meaning_1)
                matched_pattern = search_pattern.search(i.meaning_1).group(0)
                meaning_final = f"{meaning_modified}{matched_pattern}"
                i.meaning_1 = meaning_final
                print(meaning_original)
                print(meaning_modified)
                print(meaning_final)
                print()
            except AttributeError:
                print(i.lemma_1)
                print(f"[red]{i.meaning_1}")
                print()
    
    db_session.commit()

if __name__ == "__main__":
    main()
