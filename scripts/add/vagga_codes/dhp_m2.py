"""DHP meaning_2 preview: vagga → sutta-number-based code from TSV sc_code.

Reads sutta_info.tsv for DHP rows, maps chapter N → sc_code (e.g. `dhp21-32`),
uppercases the `dhp` prefix, and builds
`new_meaning_2 = "Vagga N of the Dhammapada (DHP{first}-{last})"`.

Preview only. Writes `temp/vagga_codes_DHP_m2.tsv`.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from scripts.add.vagga_codes.shared import PREVIEW_DIR, write_preview_tsv

TSV = Path("db/backup_tsv/sutta_info.tsv")
VAGGA_M1_RE = re.compile(r"Vagga\s+(\d+)", re.IGNORECASE)
CHAPTER_M2_RE = re.compile(r"Chapter\s+(\d+)", re.IGNORECASE)
SC_CODE_RE = re.compile(r"^dhp(\d+)-(\d+)$")

SC_CODE_OVERRIDES = {7: "DHP90-99"}


def load_dhp_codes() -> dict[int, str]:
    """chapter number (1..26) -> 'DHP{first}-{last}'."""
    out: dict[int, str] = {}
    with TSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["book_code"] != "DHP":
                continue
            m = re.match(r"^DHP(\d+)$", r["dpd_code"])
            if not m:
                continue
            chapter = int(m.group(1))
            sc = r["sc_code"].strip()
            mm = SC_CODE_RE.match(sc)
            if not mm:
                out[chapter] = f"BAD:{sc}"
                continue
            first, last = mm.group(1), mm.group(2)
            out[chapter] = f"DHP{first}-{last}"
    for ch, code in SC_CODE_OVERRIDES.items():
        out[ch] = code
    return out


def main() -> None:
    codes = load_dhp_codes()
    print(f"loaded {len(codes)} DHP chapter codes")
    session = get_db_session(Path("dpd.db"))
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
    rows: list[dict] = []
    for hw in headwords:
        old_m1 = hw.meaning_1 or ""
        old_m2 = hw.meaning_2 or ""
        m = VAGGA_M1_RE.search(old_m1) or CHAPTER_M2_RE.search(old_m2)
        status: str
        new_m1 = old_m1
        if not m:
            status = "no-chapter"
        else:
            chapter = int(m.group(1))
            code = codes.get(chapter)
            if code is None:
                status = f"no-tsv-row-for-chapter-{chapter}"
            elif code.startswith("BAD:"):
                status = f"bad-sc_code ({code[4:]})"
            else:
                new_m1 = f"Vagga {chapter} of the Dhammapada ({code})"
                status = "rewritten" if old_m1 != new_m1 else "unchanged"
        rows.append(
            {
                "id": hw.id,
                "lemma_1": hw.lemma_1,
                "old_family_set": hw.family_set or "",
                "new_family_set": hw.family_set or "",
                "old_meaning_1": old_m1,
                "new_meaning_1": new_m1,
                "old_meaning_lit": hw.meaning_lit or "",
                "new_meaning_lit": hw.meaning_lit or "",
                "status": status,
            }
        )
    out = PREVIEW_DIR / "vagga_codes_DHP.tsv"
    write_preview_tsv(out, rows)
    print(f"wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
