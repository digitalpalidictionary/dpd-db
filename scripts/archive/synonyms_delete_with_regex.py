#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

import re
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    lemma_clean = "paṭijānāti"
    search_term = f"( |^){lemma_clean}(,|$)"

    results = db_session \
        .query(DpdHeadword) \
        .filter(DpdHeadword.synonym.regexp_match(search_term)) \
        .all()
    
    for r in results:
        print(f"{r.lemma_1:<30}[green]{r.synonym} {len(r.synonym.split(', '))}")
        r.synonym = re.sub(search_term, "", r.synonym).strip()
        print(f"{r.lemma_1:<30}[light_green]{r.synonym} {len(r.synonym.split(', '))}")
        print()

if __name__ == "__main__":
    main()
