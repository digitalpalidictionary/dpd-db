#!/usr/bin/env python3
"""Generate a diacritic-insensitive search index for the DPD Webapp."""

import json
import unicodedata

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, FamilyRoot
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def strip_diacritics(text: str) -> str:
    """Strips diacritical marks and root signs from a Unicode string for matching."""
    # Remove root sign and spaces first
    text = text.replace("√", "").replace(" ", "")
    normalized_text = unicodedata.normalize("NFD", text)
    stripped_text = "".join(
        char for char in normalized_text if unicodedata.category(char) != "Mn"
    )
    return unicodedata.normalize("NFC", stripped_text)


def build_index(terms: set[str]) -> list[str]:
    """Builds a sorted array of 'ascii|unicode1|unicode2' strings for fast binary search."""
    index_dict = {}
    for term in terms:
        if not term:
            continue
        normalized = strip_diacritics(term).lower()
        if normalized not in index_dict:
            index_dict[normalized] = set()
        index_dict[normalized].add(term)

    # Create sorted list of "key|val1|val2..."
    sorted_index = []
    for key in sorted(index_dict.keys()):
        values = sorted(list(index_dict[key]))
        sorted_index.append(f"{key}|{'|'.join(values)}")

    return sorted_index


def main():
    pr.tic()
    pr.title("generating webapp search_index.json")
    pth = ProjectPaths()
    db_sess = get_db_session(pth.dpd_db_path)

    terms = set()

    # Aggregate Headwords
    pr.green("fetching headwords")
    headwords = db_sess.query(DpdHeadword).all()
    for hw in headwords:
        terms.add(hw.lemma_clean)
    pr.yes(len(headwords))

    # Aggregate Roots
    pr.green("fetching roots")
    roots = db_sess.query(DpdRoot).all()
    for rt in roots:
        terms.add(rt.root_clean)
    pr.yes(len(roots))

    # Aggregate Root Families
    pr.green("fetching root families")
    families = db_sess.query(FamilyRoot).all()
    for fam in families:
        terms.add(fam.root_family)
    pr.yes(len(families))

    # Build index
    pr.green("building index")
    search_index = build_index(terms)
    pr.yes(len(search_index))

    # Save to JSON
    pr.green("saving index")
    output_path = pth.webapp_static_dir / "search_index.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False, indent=None)
    pr.yes("ok")

    db_sess.close()
    pr.toc()


if __name__ == "__main__":
    main()
