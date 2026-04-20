"""KN (Khuddaka Nikāya) vagga sutta-code enrichment (preview only, no DB writes).

One module covers all the small KN books with vagga headwords:
Dhammapada, Udāna, Itivuttaka, Sutta Nipāta, Petavatthu, Vimānavatthu.

Each book has its own handler because meaning_2 patterns and code derivation
differ per book, but they all produce rows with the same schema and feed a
single merged TSV (`temp/vagga_codes_KN.tsv`).
"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from db.models import DpdHeadword
from scripts.add.vagga_codes.shared import (
    PREVIEW_DIR,
    VaggaKey,
    VaggaRun,
    chapter_to_section,
    chapter_to_vagga,
    format_range,
    normalize_family_set,
    write_preview_tsv,
)

BOOK = "KN"

CHAPTER_M2_RE = re.compile(r"Chapter\s+(\d+)")


def _base_row(hw: DpdHeadword, new_m1: str, status: str) -> dict:
    old_fs = hw.family_set or ""
    old_m1 = hw.meaning_1 or ""
    old_ml = hw.meaning_lit or ""
    return {
        "id": hw.id,
        "lemma_1": hw.lemma_1,
        "old_family_set": old_fs,
        "new_family_set": normalize_family_set(old_fs),
        "old_meaning_1": old_m1,
        "new_meaning_1": chapter_to_vagga(new_m1),
        "old_meaning_lit": old_ml,
        "new_meaning_lit": chapter_to_section(old_ml),
        "status": status,
    }


def _process_simple(
    session: Session,
    runs: dict[VaggaKey, list[VaggaRun]],
    family_set: str,
    tsv_book: str,
    display_name: str,
) -> list[dict]:
    """Standard KN handler: chapter N in m2, look up run by position, format range."""
    book_runs = runs.get((tsv_book, None), [])
    rows: list[dict] = []
    alt_family_set = family_set.replace("vaggas of the ", "vaggas of ")
    headwords = (
        session.query(DpdHeadword)
        .filter(DpdHeadword.family_set.in_([family_set, alt_family_set]))
        .order_by(DpdHeadword.id)
        .all()
    )
    for hw in headwords:
        old_m2 = hw.meaning_2 or ""
        m = CHAPTER_M2_RE.search(old_m2)
        if not m:
            rows.append(_base_row(hw, "", "no-chapter-in-meaning_2"))
            continue
        chapter = int(m.group(1))
        if not (1 <= chapter <= len(book_runs)):
            rows.append(
                _base_row(
                    hw,
                    "",
                    f"chapter-out-of-range (have {len(book_runs)})",
                )
            )
            continue
        run = book_runs[chapter - 1]
        code = format_range(tsv_book, run[0], run[1])
        new_m1 = f"Vagga {chapter} of the {display_name} ({code})"
        status = "rewritten" if (hw.meaning_1 or "") != new_m1 else "unchanged"
        rows.append(_base_row(hw, new_m1, status))
    return rows


def _process_dhp(session: Session) -> list[dict]:
    """DHP: each dpd_code IS one vagga. No TSV lookup needed — code = `DHP{N}`."""
    rows: list[dict] = []
    headwords = (
        session.query(DpdHeadword)
        .filter(
            DpdHeadword.family_set.in_(
                ["vaggas of the Dhammapada", "vaggas of Dhammapada"]
            )
        )
        .order_by(DpdHeadword.id)
        .all()
    )
    for hw in headwords:
        old_m2 = hw.meaning_2 or ""
        m = CHAPTER_M2_RE.search(old_m2)
        if not m:
            rows.append(_base_row(hw, "", "no-chapter-in-meaning_2"))
            continue
        chapter = int(m.group(1))
        if not (1 <= chapter <= 26):
            rows.append(_base_row(hw, "", "chapter-out-of-range (have 26)"))
            continue
        code = f"DHP{chapter}"
        new_m1 = f"Vagga {chapter} of the Dhammapada ({code})"
        status = "rewritten" if (hw.meaning_1 or "") != new_m1 else "unchanged"
        rows.append(_base_row(hw, new_m1, status))
    return rows


SUB_BOOKS: list[tuple[str, str, str, str]] = [
    ("DHP", "", "", "Dhammapada"),
    ("UD", "vaggas of the Udāna", "UD", "Udāna"),
    ("ITI", "vaggas of the Itivuttaka", "ITI", "Itivuttaka"),
    ("SNP", "vaggas of the Sutta Nipāta", "SNP", "Sutta Nipāta"),
    ("PV", "vaggas of the Petavatthu", "PV", "Petavatthu"),
    ("VV", "vaggas of the Vimānavatthu", "VV", "Vimānavatthu"),
]


def process(session: Session, runs: dict[VaggaKey, list[VaggaRun]]) -> list[dict]:
    all_rows: list[dict] = []
    for sub_code, family_set, tsv_book, display in SUB_BOOKS:
        if sub_code == "DHP":
            rows = _process_dhp(session)
        else:
            rows = _process_simple(session, runs, family_set, tsv_book, display)
        out = PREVIEW_DIR / f"vagga_codes_{sub_code}.tsv"
        write_preview_tsv(out, rows)
        print(f"  [{sub_code}] {len(rows)} rows -> {out}")
        all_rows += rows
    return all_rows
