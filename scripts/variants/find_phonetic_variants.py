#!/usr/bin/env python3

"""Find candidate phonetic variants in dpd.db and emit a TSV for review.

This is part 1 of issue #144 (split textual & phonetic variants). It does
NOT write to the database. It reads every ``DpdHeadword``, runs the three
detectors in ``phonetic_variant_detector.py``, collapses symmetric duplicates
to canonical pairs, and writes one block per pair into
``phonetic_variant_candidates.tsv`` sitting next to this script.

Layout: each pair is a block of rows — one row per headword in the pair
(source + any target homonyms), plus a blank separator. The rule is repeated
in column 0 for each row so the TSV can be filtered directly.

Run with::

    uv run python scripts/variants/find_phonetic_variants.py
"""

import csv
from pathlib import Path
from typing import cast

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from scripts.variants.phonetic_variant_detector import (
    HeadwordLike,
    PhoneticVariantDetector,
    PhoneticVariantPair,
)
from tools.paths import ProjectPaths
from tools.printer import printer as pr

OUTPUT_TSV: Path = Path(__file__).parent / "phonetic_variant_candidates.tsv"

TSV_HEADER: list[str] = [
    "rule",
    "lemma_1",
    "pos",
    "construction_clean",
    "meaning_combo",
    "family_root",
    "var_phonetic",
    "var_text",
    "variant",
]


def _headword_row(hw: HeadwordLike, rule: str) -> list[str]:
    return [
        rule,
        hw.lemma_1,
        hw.pos,
        hw.construction_clean,
        hw.meaning_combo,
        hw.family_root,
        hw.var_phonetic,
        hw.var_text,
        hw.variant,
    ]


def _write_tsv(path: Path, pairs: list[PhoneticVariantPair]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blank_row = [""] * len(TSV_HEADER)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(TSV_HEADER)
        for pair in pairs:
            writer.writerow(_headword_row(pair.source, pair.rule))
            for target in pair.targets:
                writer.writerow(_headword_row(target, pair.rule))
            writer.writerow(blank_row)


def main() -> None:
    pr.tic()
    pr.yellow_title("find phonetic variants")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    pr.green_title("loading headwords")
    headwords = db_session.query(DpdHeadword).all()
    pr.summary("headwords", str(len(headwords)))

    pr.green_title("running detectors")
    detector = PhoneticVariantDetector(cast(list[HeadwordLike], headwords))
    pairs = detector.detect_canonical_pairs()
    pr.summary("pairs", str(len(pairs)))

    pr.green_title("writing tsv")
    _write_tsv(OUTPUT_TSV, pairs)
    pr.summary("output", str(OUTPUT_TSV))

    db_session.close()
    pr.toc()


if __name__ == "__main__":
    main()
