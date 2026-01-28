#!/usr/bin/env python3
"""Generate a diacritic-insensitive search index for the DPD Webapp."""

import json
import re
import unicodedata

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, FamilyRoot, DbInfo
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


def build_index(terms: set[str]) -> dict[str, list[str]]:
    """Builds a dictionary mapping ASCII-normalized keys to arrays of actual Pāḷi terms."""
    index = {}
    for term in sorted(terms):
        if not term:
            continue
        normalized = strip_diacritics(term).lower()
        if normalized not in index:
            index[normalized] = []
        if term not in index[normalized]:
            index[normalized].append(term)
    return index


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

    # Aggregate Roots (using root_clean to include the √ sign)
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

    # Fetch version
    pr.green("fetching version")
    db_info = db_sess.query(DbInfo).filter(DbInfo.key == "dpd_release_version").first()
    version = db_info.value if db_info else "unknown"
    pr.yes(version)

    # Build index
    pr.green("building index")
    search_index = build_index(terms)
    pr.yes(len(terms))

    # Save index to JSON
    pr.green("saving index")
    output_path = pth.webapp_static_dir / "search_index.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False, indent=0)
    pr.yes("ok")

    # Save version to JSON
    pr.green("saving version")
    version_path = pth.webapp_static_dir / "search_index_version.json"
    with open(version_path, "w", encoding="utf-8") as f:
        json.dump({"version": version}, f)
    pr.yes("ok")

    db_sess.close()
    pr.toc()


if __name__ == "__main__":
    main()