"""Apply a per-book vagga-codes preview TSV to the DPD database.

Reads `temp/vagga_codes_<BOOK>.tsv` and writes `family_set` and `meaning_1`
for every row whose `status` is `replaced`, `appended`, or `rewritten`
and whose `new_*` differs from `old_*`. Commits once at the end.

Usage:
    uv run python -m scripts.add.vagga_codes.apply --book MN
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword

PREVIEW_DIR = Path("temp")
APPLY_STATUSES = {
    "replaced",
    "appended",
    "rewritten",
    "span-replaced",
    "span-appended",
    "no-chapter",
}
# chapter-N-not-in-cst is dynamic; matched by prefix below.
APPLY_PREFIXES = ("chapter-",)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply a vagga-codes preview TSV.")
    parser.add_argument("--book", required=True, help="Book code (e.g. MN)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Report without committing"
    )
    args = parser.parse_args()

    tsv = PREVIEW_DIR / f"vagga_codes_{args.book}.tsv"
    if not tsv.exists():
        raise SystemExit(f"Preview TSV not found: {tsv}")

    session = get_db_session(Path("dpd.db"))
    updates = 0
    skipped = 0
    with tsv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            status = row["status"]
            if status not in APPLY_STATUSES and not any(
                status.startswith(p) for p in APPLY_PREFIXES
            ):
                skipped += 1
                continue
            hw = session.get(DpdHeadword, int(row["id"]))
            if hw is None:
                print(f"  missing id {row['id']}")
                continue
            changed = False
            if (hw.family_set or "") != row["new_family_set"]:
                hw.family_set = row["new_family_set"]
                changed = True
            if (hw.meaning_1 or "") != row["new_meaning_1"]:
                hw.meaning_1 = row["new_meaning_1"]
                changed = True
            new_ml = row.get("new_meaning_lit", "")
            if new_ml and (hw.meaning_lit or "") != new_ml:
                hw.meaning_lit = new_ml
                changed = True
            if changed:
                updates += 1

    print(f"[{args.book}] updates={updates} skipped={skipped}")
    if args.dry_run:
        session.rollback()
        print("dry-run: rolled back")
    else:
        session.commit()
        print("committed")


if __name__ == "__main__":
    main()
