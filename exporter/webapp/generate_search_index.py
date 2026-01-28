#!/usr/bin/env python3
"""Generate a diacritic-insensitive search index for the DPD Webapp."""

import json
from unidecode import unidecode

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, FamilyRoot
from tools.paths import ProjectPaths

def strip_diacritics(text: str) -> str:
    """Strips diacritical marks from a Unicode string using unidecode."""
    return unidecode(text)

def build_index(terms: set[str]) -> dict[str, list[str]]:
    """Builds a dictionary mapping ASCII-normalized keys to arrays of actual Pāḷi terms."""
    index = {}
    for term in sorted(terms):
        normalized = strip_diacritics(term).lower()
        if normalized not in index:
            index[normalized] = []
        if term not in index[normalized]:
            index[normalized].append(term)
    return index

def main():
    pth = ProjectPaths()
    db_sess = get_db_session(pth.dpd_db_path)

    terms = set()

    # Aggregate Headwords
    print("Fetching headwords...")
    headwords = db_sess.query(DpdHeadword).all()
    for hw in headwords:
        terms.add(hw.lemma_clean)

    # Aggregate Roots
    print("Fetching roots...")
    roots = db_sess.query(DpdRoot).all()
    for rt in roots:
        terms.add(rt.root_no_sign)

    # Aggregate Root Families
    print("Fetching root families...")
    families = db_sess.query(FamilyRoot).all()
    for fam in families:
        terms.add(fam.root_family_clean)

    print(f"Total unique terms: {len(terms)}")

    # Build index
    search_index = build_index(terms)
    
    # Save to JSON
    output_path = pth.webapp_static_dir / "search_index.json"
    print(f"Saving search index to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False, indent=0)

    db_sess.close()
    print("Done!")

if __name__ == "__main__":
    main()