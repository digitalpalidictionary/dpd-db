"""AN vagga sutta-code enrichment (preview only, no DB writes).

AN differs from MN/SN: `meaning_1` is empty for almost all AN vagga headwords,
and the vagga descriptor sits in `meaning_2` in the form
``Chapter N of {NipātaName}, Aṅguttara Nikāya {nipata}.{range}``. We parse
`meaning_2`, look up the matching CST vagga by position within the nipāta,
and write `new_meaning_1 = "Vagga N of {NipātaName} (AN{code})"`.
"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from db.models import DpdHeadword
from scripts.add.vagga_codes.shared import (
    VaggaKey,
    VaggaRun,
    chapter_to_section,
    chapter_to_vagga,
    format_range,
    normalize_family_set,
)

BOOK = "AN"
EXCLUDE_IDS: set[int] = {17857}  # etadaggavagga 1 — free-text meaning_2, no chapter
FAMILY_SET_RE = re.compile(r"^vaggas of (?:the )?Aṅguttara Nikāya (\d+)$")
# matches the final "Chapter N of Xnipāta" in meaning_2
MEANING2_RE = re.compile(
    r"Chapter\s+(\d+)\s+of\s+(?:the\s+)?([A-Za-zĀāĪīŪūṬṭḌḍṆṇÑñṄṅṚṛṢṣŚśṀṁḶḷḤḥ]+nipāta)",
    re.UNICODE,
)
# matches the embedded range "Aṅguttara Nikāya N.first(-mid)*-last" at the end of meaning_2
RANGE_RE = re.compile(
    r"Aṅguttara\s+Nikāya\s+(\d+)\.(\d+(?:-\d+)*)",
    re.UNICODE,
)


def process(session: Session, runs: dict[VaggaKey, list[VaggaRun]]) -> list[dict]:
    rows: list[dict] = []
    headwords = (
        session.query(DpdHeadword)
        .filter(DpdHeadword.family_set.like("vaggas of%Aṅguttara Nikāya%"))
        .order_by(DpdHeadword.id)
        .all()
    )
    for hw in headwords:
        if hw.id in EXCLUDE_IDS:
            continue
        old_fs = hw.family_set or ""
        old_m1 = hw.meaning_1 or ""
        old_m2 = hw.meaning_2 or ""
        status = ""
        working_m1 = old_m1

        m_fs = FAMILY_SET_RE.match(old_fs)
        m_m2 = MEANING2_RE.search(old_m2)

        if not m_fs:
            status = "bad-family-set"
        elif not m_m2:
            status = "no-chapter-in-meaning_2"
        else:
            nipata = m_fs.group(1)
            chapter = int(m_m2.group(1))
            nipata_name = m_m2.group(2)
            an_runs = runs.get((BOOK, nipata), [])
            code: str | None = None
            if an_runs and 1 <= chapter <= len(an_runs):
                run = an_runs[chapter - 1]
                code = format_range(BOOK, run[0], run[1])
            else:
                m_range = RANGE_RE.search(old_m2)
                if m_range and m_range.group(1) == nipata:
                    parts = m_range.group(2).split("-")
                    first, last = parts[0], parts[-1]
                    code = (
                        f"AN{nipata}.{first}-{last}"
                        if first != last
                        else f"AN{nipata}.{first}"
                    )
            if code is None:
                if not an_runs:
                    status = f"no-runs-AN{nipata}"
                else:
                    status = f"chapter-out-of-range (have {len(an_runs)})"
            else:
                working_m1 = f"Vagga {chapter} of {nipata_name} ({code})"
                status = "rewritten" if old_m1 != working_m1 else "unchanged"

        new_m1 = chapter_to_vagga(working_m1)
        new_fs = normalize_family_set(old_fs)
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
