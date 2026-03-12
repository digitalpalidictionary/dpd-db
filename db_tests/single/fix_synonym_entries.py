#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Find and fix corrupted synonym, antonym, and variant entries
where values have been concatenated without a separator."""

import pyperclip
from rich import print
from rich.prompt import Prompt
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.goldendict_tools import open_in_goldendict
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    print("[bright_yellow]finding corrupted synonym, antonym and variant entries")

    pth = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)
    db: list[DpdHeadword] = db_session.query(DpdHeadword).all()

    lemma_clean_set: set[str] = {i.lemma_clean for i in db}

    for field_name in ["synonym", "antonym", "variant"]:
        print(f"\n[bright_yellow]checking {field_name} fields")
        flagged = find_invalid_entries(db, lemma_clean_set, field_name)
        if flagged:
            edit_entries(db_session, flagged, field_name)
        else:
            print(f"[green]no invalid {field_name} entries found")

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

    print(f"[cyan]found {len(flagged)} entries with invalid {field_name} values")
    return flagged


def edit_entries(
    db_session: Session,
    flagged: list[tuple[DpdHeadword, list[str]]],
    field_name: str,
) -> None:
    """Interactively edit flagged entries."""

    for counter, (headword, invalid_items) in enumerate(flagged):
        field_value: str = getattr(headword, field_name, "")

        print(f"\n[white]{counter + 1} / {len(flagged)}")
        print(f"[yellow]{headword.lemma_1:<30}[blue]{headword.pos}")
        print(f"[green]{headword.meaning_1}")
        print(f"[cyan]{field_name}: [white]{field_value}")
        print(f"[red]invalid: [white]{', '.join(invalid_items)}")

        open_in_goldendict(headword.lemma_clean)
        pyperclip.copy(field_value)

        question = "[white](e)dit, (p)ass, (b)reak"
        choice = Prompt.ask(question)

        if choice == "e":
            new_value = Prompt.ask(f"[white]new {field_name}")
            if new_value:
                new_value = ", ".join(pali_list_sorter(new_value.split(", ")))
            setattr(headword, field_name, new_value)
            db_session.commit()
            print(f"[green]updated {field_name} to: [white]{new_value}")

        elif choice == "p":
            continue

        elif choice == "b":
            break


if __name__ == "__main__":
    main()
