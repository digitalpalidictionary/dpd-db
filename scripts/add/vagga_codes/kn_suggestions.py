"""Suggest vagga headwords for KN books that have none in DPD yet.

Reads `db/backup_tsv/sutta_info.tsv` and emits proposed rows for TH, THI, JA
to `temp/vagga_codes_suggestions.tsv`. For each vagga it suggests:

- `lemma_1`      — the cst_vagga name, lowercased, trailing `o` → `a`
- `family_set`   — `"vaggas of the Theragāthā"` (etc.)
- `meaning_1`    — `"Vagga N of <NipātaName> (<BOOK><first>-<last>)"`

Books skipped (reason):
- KHP — no vagga structure in TSV (each row is a flat sutta).
- BV, CP, APA, API, NIDD1, NIDD2, PM — no `dpd_code` populated in TSV.
"""

from __future__ import annotations

import csv
import re
from collections import OrderedDict
from pathlib import Path

SUTTA_INFO_TSV = Path("db/backup_tsv/sutta_info.tsv")
OUT_TSV = Path("temp/vagga_codes_suggestions.tsv")

DPD_CODE_RE = re.compile(r"^([A-Za-z]+)(\d+)")
LEADING_NUM_RE = re.compile(r"^\d+\.\s*")


def _strip_num(name: str) -> str:
    return LEADING_NUM_RE.sub("", name).strip()


def _lemma_from_vagga(cst_vagga: str) -> str:
    """`1. Paṭhamavaggo` → `paṭhamavagga`."""
    bare = _strip_num(cst_vagga)
    if bare.endswith("o"):
        bare = bare[:-1] + "a"
    return bare[:1].lower() + bare[1:] if bare else ""


BOOKS = [
    # (book_code, section_col, vagga_col, display_name, family_set, use_section)
    ("TH", "cst_section", "cst_vagga", "Theragāthā", "vaggas of the Theragāthā", True),
    ("THI", None, "cst_vagga", "Therīgāthā", "vaggas of the Therīgāthā", False),
    ("JA", "cst_section", "cst_vagga", "Jātaka", "vaggas of the Jātaka", True),
]


def main() -> None:
    rows_by_book: dict[str, list[dict]] = OrderedDict()
    with SUTTA_INFO_TSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        all_rows = list(reader)

    for book, sec_col, vg_col, display, family_set, use_section in BOOKS:
        # Group suttas by (section, vagga) preserving order
        groups: "OrderedDict[tuple[str, str], list[str]]" = OrderedDict()
        for r in all_rows:
            if (r.get("book_code") or "").strip() != book:
                continue
            dpd_code = (r.get("dpd_code") or "").strip()
            if not dpd_code:
                continue
            section = (r.get(sec_col) or "").strip() if sec_col else ""
            vagga = (r.get(vg_col) or "").strip()
            if use_section and not section:
                continue
            if not vagga:
                continue
            groups.setdefault((section, vagga), []).append(dpd_code)

        # Number vaggas per section in encounter order
        section_counts: dict[str, int] = {}
        out_rows: list[dict] = []
        for (section, vagga), codes in groups.items():
            section_counts[section] = section_counts.get(section, 0) + 1
            chapter_n = section_counts[section]
            first, last = codes[0], codes[-1]
            m_first = DPD_CODE_RE.match(first)
            m_last = DPD_CODE_RE.match(last)
            first_n = m_first.group(2) if m_first else first
            last_n = m_last.group(2) if m_last else last
            code = (
                f"{book}{first_n}" if first_n == last_n else f"{book}{first_n}-{last_n}"
            )
            # For THI, the "vagga" IS the nipāta — number is just 1 per section
            if use_section:
                nipata_name = _strip_num(section)
                meaning_1 = f"Vagga {chapter_n} of {nipata_name} ({code})"
                fs = f"{family_set} {_strip_num(section).split()[0] if section else ''}".rstrip()
                # Actually family_set for TH/JA shouldn't include nipata number since
                # THI/Dhp/etc don't. Keep uniform: fs = family_set
                fs = family_set
            else:
                nipata_name = _strip_num(vagga)
                meaning_1 = f"Vagga 1 of {nipata_name} ({code})"
                fs = family_set
            lemma = (
                _lemma_from_vagga(vagga) if use_section else _lemma_from_vagga(vagga)
            )
            out_rows.append(
                {
                    "book": book,
                    "suggested_lemma_1": lemma,
                    "suggested_family_set": fs,
                    "suggested_meaning_1": meaning_1,
                    "cst_section": section,
                    "cst_vagga": vagga,
                    "first_code": first,
                    "last_code": last,
                    "sutta_count": str(len(codes)),
                }
            )
        rows_by_book[book] = out_rows

    # Write merged TSV
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "book",
        "suggested_lemma_1",
        "suggested_family_set",
        "suggested_meaning_1",
        "cst_section",
        "cst_vagga",
        "first_code",
        "last_code",
        "sutta_count",
    ]
    with OUT_TSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for book, rows in rows_by_book.items():
            for r in rows:
                w.writerow(r)
            print(f"[{book}] {len(rows)} suggested vaggas")
    print(f"merged -> {OUT_TSV}")


if __name__ == "__main__":
    main()
