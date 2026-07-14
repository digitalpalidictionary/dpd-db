#!/usr/bin/env python3
"""Remove tokens from `DpdHeadword.variant` that already appear in
`synonym`, `var_phonetic`, or `var_text`.

The `variant` column is a legacy catch-all; tokens that have since been
classified into one of the three semantic fields are redundant there.

Default mode is a dry run — pass `--apply` to commit changes.
"""

from __future__ import annotations

import argparse

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.synonym_variant import split_field


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="commit changes to the db (default: dry run)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="cap dry-run output to N entries (default: 50)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="show every affected entry (overrides --limit)",
    )
    return parser.parse_args()


def main() -> None:
    pr.tic()
    args = parse_args()

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    headwords: list[DpdHeadword] = db_session.query(DpdHeadword).all()

    pr.green_tmr("scanning variant field for duplicates")
    affected: list[tuple[DpdHeadword, set[str], set[str]]] = []
    total_removed = 0
    fully_emptied = 0

    for hw in headwords:
        variant_set = split_field(hw.variant)
        if not variant_set:
            continue
        related = (
            set(hw.synonym_list)
            | split_field(hw.var_phonetic)
            | split_field(hw.var_text)
        )
        duplicates = variant_set & related
        if not duplicates:
            continue
        remainder = variant_set - duplicates
        affected.append((hw, duplicates, remainder))
        total_removed += len(duplicates)
        if not remainder:
            fully_emptied += 1

    pr.yes(str(len(affected)))

    show = affected if args.all else affected[: args.limit]
    for hw, dupes, remainder in show:
        dupes_sorted = pali_list_sorter(dupes)
        rem_sorted = pali_list_sorter(remainder)
        print(
            f"[yellow]{hw.lemma_1}[/yellow]  "
            f"[red]- {dupes_sorted}[/red]  "
            f"[green]= {rem_sorted}[/green]"
        )
    if not args.all and len(affected) > args.limit:
        print(
            f"[dim]... {len(affected) - args.limit} more (use --all to see them)[/dim]"
        )

    print()
    pr.summary("headwords affected", str(len(affected)))
    pr.summary("tokens to remove", str(total_removed))
    pr.summary("variant becomes empty", str(fully_emptied))

    if not args.apply:
        print("\n[bright_yellow]dry run — pass --apply to commit changes")
        pr.toc()
        return

    if not affected:
        print("\n[green]nothing to apply")
        pr.toc()
        return

    confirm = input(f"\nApply {len(affected)} changes to db? (y/N): ").strip().lower()
    if confirm != "y":
        print("[red]aborted")
        pr.toc()
        return

    pr.green_tmr("applying changes")
    for hw, _dupes, remainder in affected:
        hw.variant = ", ".join(pali_list_sorter(remainder))
    db_session.commit()
    pr.yes("done")

    pr.toc()


if __name__ == "__main__":
    main()
