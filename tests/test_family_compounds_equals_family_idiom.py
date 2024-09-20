#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

import re
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.db_search_string import db_search_string


def main():
    print("[yellow]finding difference between family_compound and family_idioms")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    
    print(f"[green]{'family_compound != family_idioms':<40}", end="")
    not_equal = []
    for i in db:
        if (
            not re.findall(r"\bcomp\b", i.grammar)
            and i.pos not in ["idiom", "sandhi"]
            and i.family_compound
            and " " not in i.family_compound  
            and i.family_idioms 
            and i.family_idioms != i.family_compound
        ):
           not_equal.append(i.lemma_1)

    print(f"{len(not_equal):>10}")
    if not_equal:
        print(db_search_string(not_equal))
        return
    
    counter = 0
    for i in db:
        if (
            not re.findall(r"\bcomp\b", i.grammar)
            and i.pos not in ["idiom", "sandhi"]
            and i.family_compound
            and " " not in i.family_compound
            and not i.family_idioms
        ):
            i.family_idioms = i.family_compound
            print(i)
            counter+=1
    
    print(f"[green]{'family_idioms empty':<40}", end="")
    print(f"{counter:>10}")

    db_session.commit()


if __name__ == "__main__":
    main()
