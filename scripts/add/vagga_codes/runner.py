"""CLI runner for per-book vagga-code previews. No DB writes."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from db.db_helpers import get_db_session
from scripts.add.vagga_codes import an, kn, mn, sn
from scripts.add.vagga_codes.shared import (
    PREVIEW_DIR,
    load_vagga_runs,
    write_preview_tsv,
)

BOOKS = {
    "MN": mn,
    "SN": sn,
    "AN": an,
    "KN": kn,
}


def run_book(book: str, session, runs) -> list[dict]:
    module = BOOKS[book]
    rows = module.process(session, runs)
    out = PREVIEW_DIR / f"vagga_codes_{book}.tsv"
    write_preview_tsv(out, rows)
    counts = Counter(r["status"] for r in rows)
    print(f"[{book}] {len(rows)} rows -> {out}")
    for status, n in sorted(counts.items()):
        print(f"    {status:20s} {n}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate per-book vagga sutta-code previews (no DB writes)."
    )
    parser.add_argument(
        "--book",
        choices=sorted(BOOKS.keys()),
        help="Generate preview for a single book.",
    )
    parser.add_argument("--all", action="store_true", help="Run every registered book.")
    args = parser.parse_args()
    if not args.book and not args.all:
        parser.error("specify --book <CODE> or --all")

    session = get_db_session(Path("dpd.db"))
    runs = load_vagga_runs()

    selected = sorted(BOOKS) if args.all else [args.book]
    all_rows: list[dict] = []
    for book in selected:
        rows = run_book(book, session, runs)
        for r in rows:
            r_with_book = {"book": book, **r}
            all_rows.append(r_with_book)

    if args.all:
        merged = PREVIEW_DIR / "vagga_codes_all.tsv"
        import csv as _csv

        merged.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "book",
            "id",
            "lemma_1",
            "old_family_set",
            "new_family_set",
            "old_meaning_1",
            "new_meaning_1",
            "old_meaning_lit",
            "new_meaning_lit",
            "status",
        ]
        from scripts.add.vagga_codes.shared import _sort_key

        all_rows_sorted = sorted(all_rows, key=_sort_key)
        with merged.open("w", encoding="utf-8", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            w.writeheader()
            for r in all_rows_sorted:
                w.writerow({k: r.get(k, "") for k in fieldnames})
        print(f"merged -> {merged}")


if __name__ == "__main__":
    main()
