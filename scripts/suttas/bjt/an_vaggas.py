"""Collapse BJT an.tsv to one row per vagga group and write an_vaggas.tsv."""

import csv
from pathlib import Path

from tools.printer import printer as pr

BJT_AN_TSV = Path("scripts/suttas/bjt/an.tsv")
OUT_PATH = Path("scripts/suttas/bjt/an_vaggas.tsv")

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


def _group_key(row: dict[str, str]) -> tuple[str, ...]:
    book = row.get("bjt_book", "")
    minor = row.get("bjt_minor_section", "")
    vagga = row.get("bjt_vagga", "")
    sutta_code = row.get("bjt_sutta_code", "")
    # Include the chapter-level prefix of the sutta code (book.pannasaka.vagga)
    # so sub-vaggas that share the same bjt_vagga label (e.g. AN1 ch14 etadaggapāḷi)
    # are not collapsed into a single row.
    parts = sutta_code.rstrip(".").split(".")
    chapter_key = ".".join(parts[:3]) if len(parts) >= 4 else ""
    return (book, minor, vagga, chapter_key)


def extract() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    last_key: tuple[str, ...] | None = None

    with BJT_AN_TSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            key = _group_key(row)
            if key == last_key:
                continue
            last_key = key
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
                    "bjt_book": row.get("bjt_book", ""),
                    "bjt_minor_section": row.get("bjt_minor_section", ""),
                    "bjt_vagga": row.get("bjt_vagga", ""),
                    "bjt_sutta": row.get("bjt_sutta", ""),
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
    pr.yellow_title("extract AN vaggas — BJT")
    pr.green_tmr("extracting")
    rows = extract()
    pr.yes(str(len(rows)))
    pr.green_tmr(f"saving {OUT_PATH}")
    save(rows)
    pr.yes("done")
    pr.toc()


if __name__ == "__main__":
    main()
