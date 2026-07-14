"""MN vagga sutta-code enrichment (preview only, no DB writes)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from db.models import DpdHeadword
from scripts.add.vagga_codes.shared import (
    VaggaKey,
    VaggaRun,
    chapter_to_section,
    chapter_to_vagga,
    format_range,
    normalize_family_set,
    parse_chapter,
    strip_trailing_code,
)

BOOK = "MN"
FAMILY_SET = "chapters of the Majjhima Nikāya"
NEW_FAMILY_SET = "vaggas of Majjhima Nikāya"


def process(session: Session, runs: dict[VaggaKey, list[VaggaRun]]) -> list[dict]:
    rows: list[dict] = []
    mn_runs = runs.get((BOOK, None), [])
    headwords = (
        session.query(DpdHeadword)
        .filter(
            DpdHeadword.family_set.in_(
                [FAMILY_SET, "vaggas of the Majjhima Nikāya", NEW_FAMILY_SET]
            )
        )
        .order_by(DpdHeadword.id)
        .all()
    )
    for hw in headwords:
        old_fs = hw.family_set or ""
        old_m1 = hw.meaning_1 or ""
        chapter = parse_chapter(old_m1)
        status: str
        working = old_m1
        if chapter is None:
            status = "no-chapter"
        elif not (1 <= chapter <= len(mn_runs)):
            status = "chapter-out-of-range"
        else:
            run = mn_runs[chapter - 1]
            code = format_range(BOOK, run[0], run[1])
            _ = run[2:]  # name/chapter unused for MN
            base = strip_trailing_code(old_m1)
            working = f"{base} ({code})"
            status = "replaced" if old_m1 != base else "appended"
        new_m1 = chapter_to_vagga(working)
        new_fs = (
            NEW_FAMILY_SET if old_fs == FAMILY_SET else normalize_family_set(old_fs)
        )
        # MN may already be committed with "vaggas of the Majjhima Nikāya" — still strip `the`
        if old_fs == "vaggas of the Majjhima Nikāya":
            new_fs = NEW_FAMILY_SET
        if status in ("appended", "replaced") and new_m1 == old_m1 and new_fs == old_fs:
            status = "unchanged"
        old_ml = hw.meaning_lit or ""
        new_ml = chapter_to_section(old_ml)
        rows.append(
            {
                "id": hw.id,
                "lemma_1": hw.lemma_1,
                "old_family_set": old_fs,
                "new_family_set": new_fs,
                "old_meaning_1": old_m1,
                "new_meaning_1": new_m1,
                "old_meaning_lit": old_ml,
                "new_meaning_lit": new_ml,
                "status": status,
            }
        )
    return rows
