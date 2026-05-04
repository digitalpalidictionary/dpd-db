"""Extract AN nipāta rows from DPR listam.js into a TSV.

One row per book index (0–10 = AN1–AN11), using the first vagga entry of each book.
"""

import csv
import re
from pathlib import Path

from tools.printer import printer as pr

DPR_LISTAM = Path("../../2_Resources/Code/digitalpalireader/_dprhtml/js/listam.js")
OUT_PATH = Path("scripts/suttas/dpr/an_nipatas.tsv")

BASE_URL = "https://www.digitalpalireader.online/_dprhtml/index.html?loc="

FIELDNAMES = [
    "book",
    "book_code",
    "dpd_code",
    "dpr_code",
    "dpr_link",
    "sc_code",
]

# First entry of each book: [book][0][0][0][0]
FIRST_RE = re.compile(r"DPR_G\.amlist\[(\d+)\]\[0\]\[0\]\[0\]\[0\]\s*=\s*'([\d-]+)'")


def extract() -> list[dict[str, str]]:
    content = DPR_LISTAM.read_text(encoding="utf-8")
    seen: set[int] = set()
    rows: list[dict[str, str]] = []

    for m in FIRST_RE.finditer(content):
        book_idx = int(m.group(1))
        if book_idx in seen:
            continue
        seen.add(book_idx)

        first_sutta_raw = m.group(2)
        first_sutta = first_sutta_raw.split("-")[0]
        nipata = book_idx + 1
        dpr_code = f"AN{nipata}.{first_sutta}"
        loc = f"a.{book_idx}.0.0.0.0.0.m"
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

    rows.sort(key=lambda r: int(re.sub(r"\D", "", r["dpr_code"].split(".")[0])))
    return rows


def save(rows: list[dict[str, str]]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    pr.tic()
    pr.yellow_title("extract AN nipātas — DPR")
    pr.green_tmr("extracting")
    rows = extract()
    pr.yes(str(len(rows)))
    pr.green_tmr(f"saving {OUT_PATH}")
    save(rows)
    pr.yes("done")
    pr.toc()


if __name__ == "__main__":
    main()
