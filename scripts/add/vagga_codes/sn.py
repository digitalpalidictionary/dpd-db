"""SN vagga sutta-code enrichment (preview only, no DB writes)."""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from sqlalchemy import or_

from db.models import DpdHeadword
from scripts.add.vagga_codes.shared import (
    VaggaKey,
    VaggaRun,
    chapter_to_section,
    chapter_to_vagga,
    format_range,
    load_section_spans,
    normalize_family_set,
    parse_chapter,
    strip_trailing_code,
)

BOOK = "SN"
FAMILY_SET_RE = re.compile(r"^vaggas of (?:the )?Saṃyutta Nikāya (\d+)$")
BOOK_CLAUSE_RE = re.compile(r",\s*Book\s+\d+\s+of\s+the\s+Saṃyutta\s+Nikāya")


def process(session: Session, runs: dict[VaggaKey, list[VaggaRun]]) -> list[dict]:
    rows: list[dict] = []
    spans = load_section_spans()
    headwords = (
        session.query(DpdHeadword)
        .filter(
            DpdHeadword.lemma_1.like("%vagga%"),
            or_(
                DpdHeadword.family_set.like("vaggas of%Saṃyutta Nikāya%"),
                DpdHeadword.meaning_1.like("%Saṃyutta%"),
                DpdHeadword.meaning_2.like("%Saṃyutta%"),
            ),
            DpdHeadword.family_set != "parts of the Saṃyutta Nikāya",
            ~DpdHeadword.meaning_1.like("Part % of the Saṃyutta Nikāya%"),
        )
        .order_by(DpdHeadword.id)
        .all()
    )
    for hw in headwords:
        old_fs = hw.family_set or ""
        old_m1 = hw.meaning_1 or ""
        status = ""
        working = old_m1

        m = FAMILY_SET_RE.match(old_fs)
        chapter = parse_chapter(old_m1)

        if not m:
            status = "bad-family-set"
        else:
            samyutta = m.group(1)
            sn_runs = runs.get((BOOK, samyutta), [])
            span = spans.get((BOOK, samyutta))
            if not sn_runs and span is not None:
                code = format_range(BOOK, span[0], span[1])
                base = strip_trailing_code(old_m1)
                working = f"{base} ({code})"
                status = "span-replaced" if old_m1 != base else "span-appended"
            elif not sn_runs:
                status = f"no-data-SN{samyutta}"
            elif chapter is None:
                status = "no-chapter"
            else:
                run = next((r for r in sn_runs if r[3] == chapter), None)
                if run is None:
                    have = sorted(r[3] for r in sn_runs if r[3] is not None)
                    status = f"chapter-{chapter}-not-in-cst (have {have})"
                else:
                    code = format_range(BOOK, run[0], run[1])
                    base = strip_trailing_code(old_m1)
                    working = f"{base} ({code})"
                    status = "replaced" if old_m1 != base else "appended"

        working = BOOK_CLAUSE_RE.sub("", working)
        new_m1 = chapter_to_vagga(working)
        new_fs = normalize_family_set(old_fs)
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
