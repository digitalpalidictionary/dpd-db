#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Find and fix corrupted synonym, antonym, and variant entries
where values have been concatenated without a separator."""

import json
from pathlib import Path

import pyperclip
from prompt_toolkit import prompt as pt_prompt
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr

FIXES_PATH = Path(__file__).parent / "fix_synonym_entries.json"


def load_known_fixes() -> dict[str, str]:
    """Load previously saved fixes from JSON."""
    if FIXES_PATH.exists():
        with open(FIXES_PATH) as f:
            return json.load(f)
    return {}


def save_known_fixes(known_fixes: dict[str, str]) -> None:
    """Save fixes to JSON."""
    with open(FIXES_PATH, "w") as f:
        json.dump(known_fixes, f, ensure_ascii=False, indent=2)


def main() -> None:
    pr.tic()
    pr.yellow_title("finding corrupted synonym, antonym and variant entries")

    pth = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)
    db: list[DpdHeadword] = db_session.query(DpdHeadword).all()

    lemma_clean_set: set[str] = {i.lemma_clean for i in db}
    lookup_set: set[str] = {
        row.lookup_key for row in db_session.query(Lookup.lookup_key).all()
    }
    known_fixes = load_known_fixes()

    for field_name in ["synonym", "antonym", "variant"]:
        pr.green_title(f"checking {field_name} fields")
        corrupted, non_headwords = find_invalid_entries(
            db, lemma_clean_set, lookup_set, field_name
        )

        # pass 1: fix concatenated entries
        if corrupted:
            pr.green_title(f"pass 1: fixing concatenated {field_name} entries")
            fix_concatenated(
                db_session, lemma_clean_set, known_fixes, corrupted, field_name
            )
        else:
            pr.green(f"no concatenated {field_name} entries found")

        # pass 2: review non-headword entries
        if non_headwords:
            pr.green_title(f"pass 2: reviewing non-headword {field_name} entries")
            review_non_headwords(non_headwords, field_name)
        else:
            pr.green(f"no non-headword {field_name} entries found")

    save_known_fixes(known_fixes)
    pr.toc()


def find_invalid_entries(
    db: list[DpdHeadword],
    lemma_clean_set: set[str],
    lookup_set: set[str],
    field_name: str,
) -> tuple[
    list[tuple[DpdHeadword, list[str]]],
    list[tuple[DpdHeadword, list[str]]],
]:
    """Find entries where values are not in lemma_clean_set.

    Returns two lists:
    - corrupted: items not in lemma_clean_set AND not in lookup (likely concatenated)
    - non_headwords: items in lookup but not in lemma_clean_set (real words, not headwords)
    """

    corrupted: list[tuple[DpdHeadword, list[str]]] = []
    non_headwords: list[tuple[DpdHeadword, list[str]]] = []

    for i in db:
        field_value: str = getattr(i, field_name, "")
        if not field_value:
            continue

        items = field_value.split(", ")
        corrupt_items = [
            item
            for item in items
            if item not in lemma_clean_set and item not in lookup_set
        ]
        non_headword_items = [
            item for item in items if item not in lemma_clean_set and item in lookup_set
        ]

        if corrupt_items:
            corrupted.append((i, corrupt_items))
        if non_headword_items:
            non_headwords.append((i, non_headword_items))

    pr.summary(f"concatenated {field_name}", len(corrupted))
    pr.summary(f"non-headword {field_name}", len(non_headwords))
    return corrupted, non_headwords


def fix_concatenated(
    db_session: Session,
    lemma_clean_set: set[str],
    known_fixes: dict[str, str],
    flagged: list[tuple[DpdHeadword, list[str]]],
    field_name: str,
) -> None:
    """Interactively fix concatenated entries."""

    for counter, (headword, invalid_items) in enumerate(flagged):
        field_value: str = getattr(headword, field_name, "")
        current_items: list[str] = field_value.split(", ")

        remaining = len(flagged) - counter - 1
        pr.green(f"{counter + 1} / {len(flagged)} ({remaining} remaining)")
        pr.white(f"{headword.lemma_1:<30}{headword.pos}")
        pr.green(f"{headword.meaning_1}")
        pr.white(f"{field_name}: {field_value}")
        pr.amber(f"invalid: {', '.join(invalid_items)}")

        changed = False
        for bad_item in invalid_items:
            if bad_item in known_fixes:
                fixed = known_fixes[bad_item]
                pr.green(f"auto-fix: {bad_item} → {fixed}")
                fixed_parts = [p.strip() for p in fixed.split(", ") if p.strip()]
                idx = current_items.index(bad_item)
                current_items[idx : idx + 1] = fixed_parts
                changed = True
                continue

            pyperclip.copy(bad_item)
            pr.amber("add ', ' to split the word (enter to skip)")
            fixed = pt_prompt("  → ", default=bad_item)

            if fixed == bad_item:
                continue

            fixed_parts = [p.strip() for p in fixed.split(", ") if p.strip()]

            still_invalid = [p for p in fixed_parts if p not in lemma_clean_set]
            if still_invalid:
                pr.red(f"still invalid: {', '.join(still_invalid)}")
                pr.amber("skipping this fix\n")
                continue

            idx = current_items.index(bad_item)
            current_items[idx : idx + 1] = fixed_parts
            changed = True

            known_fixes[bad_item] = fixed
            save_known_fixes(known_fixes)

        if changed:
            deduped = list(dict.fromkeys(current_items))
            sorted_items = pali_list_sorter(deduped)
            new_value = ", ".join(sorted_items)
            pr.white(f"{field_name}: {new_value}\n")
            setattr(headword, field_name, new_value)
            db_session.commit()


def review_non_headwords(
    flagged: list[tuple[DpdHeadword, list[str]]],
    field_name: str,
) -> None:
    """Review entries with non-headword values. Copy to clipboard for manual fixing."""

    for counter, (headword, non_hw_items) in enumerate(flagged):
        field_value: str = getattr(headword, field_name, "")

        remaining = len(flagged) - counter - 1
        pr.green(f"{counter + 1} / {len(flagged)} ({remaining} remaining)")
        pr.white(f"{headword.lemma_1:<30}{headword.pos}")
        pr.green(f"{headword.meaning_1}")
        pr.white(f"{field_name}: {field_value}")
        pr.amber(f"non-headword: {', '.join(non_hw_items)}")

        pyperclip.copy(", ".join(non_hw_items))


if __name__ == "__main__":
    main()
