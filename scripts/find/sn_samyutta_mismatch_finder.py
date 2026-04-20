"""Find SN headwords where the SN number in meaning_1/meaning_2 (e.g. `SN45.1-12`)
does not match the saṃyutta number declared in family_set
(e.g. `suttas of Saṃyutta Nikāya 50`).

Writes mismatches to `temp/sn_samyutta_mismatch.tsv`.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword

FAMILY_SET_RE = re.compile(r"Saṃyutta\s+Nikāya\s+(\d+)", re.UNICODE)
SN_CODE_RE = re.compile(r"\bSN\s*(\d+)(?:\.\d[\d\-]*)?", re.UNICODE)

OUT = Path("temp/sn_samyutta_mismatch.tsv")


def main() -> None:
    session = get_db_session(Path("dpd.db"))
    headwords = (
        session.query(DpdHeadword)
        .filter(DpdHeadword.family_set.like("%Saṃyutta Nikāya%"))
        .order_by(DpdHeadword.id)
        .all()
    )

    rows: list[dict] = []
    for hw in headwords:
        fs = hw.family_set or ""
        m1 = hw.meaning_1 or ""
        m2 = hw.meaning_2 or ""

        fs_match = FAMILY_SET_RE.search(fs)
        m1_match = SN_CODE_RE.search(m1)
        m2_match = SN_CODE_RE.search(m2)

        fs_num = fs_match.group(1) if fs_match else None
        m1_num = m1_match.group(1) if m1_match else None
        m2_num = m2_match.group(1) if m2_match else None

        present = [n for n in (fs_num, m1_num, m2_num) if n is not None]
        if len(set(present)) <= 1:
            continue

        rows.append(
            {
                "id": hw.id,
                "lemma_1": hw.lemma_1,
                "fs_num": fs_num or "",
                "m1_num": m1_num or "",
                "m2_num": m2_num or "",
                "family_set": fs,
                "meaning_1": m1,
                "meaning_2": m2,
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=[
                "id",
                "lemma_1",
                "fs_num",
                "m1_num",
                "m2_num",
                "family_set",
                "meaning_1",
                "meaning_2",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"scanned {len(headwords)} SN headwords")
    print(f"mismatches: {len(rows)} -> {OUT}")


if __name__ == "__main__":
    main()
