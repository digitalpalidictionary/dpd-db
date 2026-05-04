"""Extract AN vagga rows from DPR listam.js into a TSV.

amlist[book][pannasaka][vagga][section] structure:
- Regular vaggas: one sutta per section → emit only section 0
- Chapter vaggas (e.g. Etadaggavaggo): each section is a sub-vagga with
  multiple suttas → emit one row per section

URL format: a.{book}.0.0.{pannasaka}.{vagga}.{section}.m
"""

import csv
import re
from pathlib import Path

from tools.printer import printer as pr
from tools.sort_naturally import alpha_num_key

DPR_LISTAM = Path("../../2_Resources/Code/digitalpalireader/_dprhtml/js/listam.js")
OUT_PATH = Path("scripts/suttas/dpr/an_vaggas.tsv")

BASE_URL = "https://www.digitalpalireader.online/_dprhtml/index.html?loc="

FIELDNAMES = [
    "book",
    "book_code",
    "dpd_code",
    "dpr_code",
    "dpr_link",
    "sc_code",
]

# Matches the first element of any section: [book][pannasaka][vagga][section][0]
FIRST_RE = re.compile(
    r"DPR_G\.amlist\[(\d+)\]\[(\d+)\]\[(\d+)\]\[(\d+)\]\[0\]\s*=\s*'([\d-]+)'"
)
# Marks a section as multi-sutta (sub-vagga) when element [1] exists
MULTI_RE = re.compile(r"DPR_G\.amlist\[(\d+)\]\[(\d+)\]\[(\d+)\]\[(\d+)\]\[1\]\s*=")


def extract() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    content = DPR_LISTAM.read_text(encoding="utf-8")

    multi_sections: set[tuple[int, int, int, int]] = set()
    for m in MULTI_RE.finditer(content):
        key = (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
        multi_sections.add(key)

    for m in FIRST_RE.finditer(content):
        book_idx = int(m.group(1))
        pannasaka_idx = int(m.group(2))
        vagga_idx = int(m.group(3))
        section_idx = int(m.group(4))
        first_sutta_raw = m.group(5)

        key = (book_idx, pannasaka_idx, vagga_idx, section_idx)
        if section_idx > 0 and key not in multi_sections:
            continue

        first_sutta = first_sutta_raw.split("-")[0]
        nipata = book_idx + 1
        dpr_code = f"AN{nipata}.{first_sutta}"
        loc = f"a.{book_idx}.0.0.{pannasaka_idx}.{vagga_idx}.{section_idx}.m"
        rows.append(
            {
                "book": "Aṅguttara Nikāya",
                "book_code": "AN",
                "dpd_code": "",
                "dpr_code": dpr_code,
                "dpr_link": f"{BASE_URL}{loc}",
                "sc_code": "",
            }
        )

    rows.sort(key=lambda r: alpha_num_key(r["dpr_code"]))
    return rows


def save(rows: list[dict[str, str]]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    pr.tic()
    pr.yellow_title("extract AN vaggas — DPR")
    pr.green_tmr("extracting")
    rows = extract()
    pr.yes(str(len(rows)))
    pr.green_tmr(f"saving {OUT_PATH}")
    save(rows)
    pr.yes("done")
    pr.toc()


if __name__ == "__main__":
    main()
