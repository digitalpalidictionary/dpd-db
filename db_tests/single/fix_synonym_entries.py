#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Find and fix corrupted synonym, antonym, and variant entries
where values have been concatenated without a separator."""

import pyperclip
from prompt_toolkit import prompt as pt_prompt
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    pr.yellow_title("finding corrupted synonym, antonym and variant entries")

    pth = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)
    db: list[DpdHeadword] = db_session.query(DpdHeadword).all()

    lemma_clean_set: set[str] = {i.lemma_clean for i in db}

    for field_name in ["synonym", "antonym", "variant"]:
        pr.green_title(f"checking {field_name} fields")
        flagged = find_invalid_entries(db, lemma_clean_set, field_name)
        if flagged:
            edit_entries(db_session, lemma_clean_set, flagged, field_name)
        else:
            pr.green(f"no invalid {field_name} entries found")

    pr.toc()


def find_invalid_entries(
    db: list[DpdHeadword],
    lemma_clean_set: set[str],
    field_name: str,
) -> list[tuple[DpdHeadword, list[str]]]:
    """Find entries where any value in the field is not in lemma_clean_set."""

    flagged: list[tuple[DpdHeadword, list[str]]] = []

    for i in db:
        field_value: str = getattr(i, field_name, "")
        if not field_value:
            continue

        items = field_value.split(", ")
        invalid = [item for item in items if item not in lemma_clean_set]

        if invalid:
            flagged.append((i, invalid))

    pr.summary(f"invalid {field_name} entries", len(flagged))
    return flagged


def edit_entries(
    db_session: Session,
    lemma_clean_set: set[str],
    flagged: list[tuple[DpdHeadword, list[str]]],
    field_name: str,
) -> None:
    """Interactively fix flagged entries.

    For each invalid item, pre-fill it in the terminal so the user can
    arrow-key to the right spot and insert ', ' to split it.
    The fixed parts replace the bad item, the full list is deduped,
    sorted, and saved.
    """

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
            pyperclip.copy(bad_item)
            pr.amber("add ', ' to split the word (enter to skip)")
            fixed = pt_prompt("  → ", default=bad_item)

            if fixed == bad_item:
                continue

            fixed_parts = [p.strip() for p in fixed.split(", ") if p.strip()]

            still_invalid = [p for p in fixed_parts if p not in lemma_clean_set]
            if still_invalid:
                pr.red(f"still invalid: {', '.join(still_invalid)}")
                pr.amber("skipping this fix")
                continue

            idx = current_items.index(bad_item)
            current_items[idx : idx + 1] = fixed_parts
            changed = True

        if changed:
            deduped = list(dict.fromkeys(current_items))
            sorted_items = pali_list_sorter(deduped)
            new_value = ", ".join(sorted_items)
            pr.white(f"{field_name}: {new_value}\n")
            setattr(headword, field_name, new_value)
            db_session.commit()


if __name__ == "__main__":
    main()
