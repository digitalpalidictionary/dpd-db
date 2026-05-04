"""Collapse BJT an.tsv to one row per nipāta and write an_nipatas.tsv."""

import csv
from pathlib import Path

from tools.printer import printer as pr

BJT_AN_TSV = Path("scripts/suttas/bjt/an.tsv")
OUT_PATH = Path("scripts/suttas/bjt/an_nipatas.tsv")

FIELDNAMES = [
    "book",
    "book_code",
    "dpd_code",
    "bjt_sutta_code",
    "bjt_web_code",
    "bjt_filename",
    "bjt_book_id",
    "bjt_page_num",
    "bjt_page_offset",
    "bjt_piṭaka",
    "bjt_nikāya",
    "bjt_major_section",
    "bjt_book",
    "bjt_minor_section",
    "bjt_vagga",
    "bjt_sutta",
]


def extract() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    with BJT_AN_TSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            bjt_book = row.get("bjt_book", "")
            if bjt_book in seen:
                continue
            seen.add(bjt_book)
            rows.append(
                {
                    "book": "Aṅguttara Nikāya",
                    "book_code": "AN",
                    "dpd_code": "",
                    "bjt_sutta_code": row.get("bjt_sutta_code", ""),
                    "bjt_web_code": row.get("bjt_web_code", ""),
                    "bjt_filename": row.get("bjt_filename", ""),
                    "bjt_book_id": row.get("bjt_book_id", ""),
                    "bjt_page_num": row.get("bjt_page_num", ""),
                    "bjt_page_offset": row.get("bjt_page_offset", ""),
                    "bjt_piṭaka": row.get("bjt_piṭaka", ""),
                    "bjt_nikāya": row.get("bjt_nikāya", ""),
                    "bjt_major_section": row.get("bjt_major_section", ""),
                    "bjt_book": bjt_book,
                    "bjt_minor_section": "",
                    "bjt_vagga": "",
                    "bjt_sutta": "",
                }
            )
    return rows


def save(rows: list[dict[str, str]]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    pr.tic()
    pr.yellow_title("extract AN nipātas — BJT")
    pr.green_tmr("extracting")
    rows = extract()
    pr.yes(str(len(rows)))
    pr.green_tmr(f"saving {OUT_PATH}")
    save(rows)
    pr.yes("done")
    pr.toc()


if __name__ == "__main__":
    main()
