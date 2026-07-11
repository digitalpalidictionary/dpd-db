#!/usr/bin/env python3

"""Find duplicate or near-duplicate examples in example_1 and example_2.

Flags identical pairs and similar pairs above a configurable threshold.
Offers delete/swap/exception actions for similar entries.
"""

import json
from difflib import SequenceMatcher

import pyperclip
from rich import print
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class GlobalVars:
    pth: ProjectPaths
    db_session: Session
    db: list[DpdHeadword]
    threshold: float
    exceptions: list[int]
    exit: bool

    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.db_session.query(DpdHeadword).all()
        self.threshold, self.exceptions = self.load_config()
        self.exit = False

    def load_config(self) -> tuple[float, list[int]]:
        if self.pth.example_dupes_config_path.exists():
            with open(self.pth.example_dupes_config_path, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("threshold", 0.81), data.get("exceptions", [])
        return 0.81, []

    def save_config(self) -> None:
        with open(self.pth.example_dupes_config_path, "w", encoding="utf-8") as f:
            json.dump(
                {"threshold": self.threshold, "exceptions": self.exceptions},
                f,
                indent=2,
            )

    def add_exception(self, id_: int) -> None:
        self.exceptions.append(id_)
        self.save_config()


def paragraphs_are_similar(para1: str, para2: str, threshold: float) -> bool:
    """Return True if two paragraphs are above the similarity threshold."""
    matcher = SequenceMatcher(None, para1, para2)
    return matcher.ratio() >= threshold


def main() -> None:
    pr.tic()
    print("[bright_yellow]find duplicate or similar examples")
    g = GlobalVars()

    for i in g.db:
        if g.exit:
            break
        if i.id in g.exceptions:
            continue
        if not (i.meaning_1 and i.example_1 and i.example_2):
            continue

        # test if identical
        if i.example_1 == i.example_2:
            print()
            print(f"{i.id:<10}{i.lemma_1}")
            print("[white]examples are identical")
            pyperclip.copy(i.lemma_1)
            print(
                "[yellow]e[white]xception "
                "[yellow]d[white]elete "
                "[yellow]q[white]uit "
                "or Enter for next: ",
                end="",
            )
            choice = input()
            if choice == "e":
                g.add_exception(i.id)
            elif choice == "d":
                i.source_2 = ""
                i.sutta_2 = ""
                i.example_2 = ""
                g.db_session.commit()
            elif choice == "q":
                g.exit = True
            continue

        # test if similar
        if paragraphs_are_similar(i.example_1, i.example_2, g.threshold):
            print()
            print(f"{i.id:<10}{i.lemma_1}")
            print(f"[dark_green]{i.source_1} {i.sutta_1}")
            print(f"[green]{i.example_1}")
            print(f"[blue]{i.source_2} {i.sutta_2}")
            print(f"[cyan]{i.example_2}")
            pyperclip.copy(i.lemma_1)
            print()
            print(
                "[yellow]e[white]xception "
                "[yellow]d[white]elete "
                "[yellow]s[white]wap "
                "[yellow]q[white]uit "
                "or Enter for next: ",
                end="",
            )
            choice = input()
            if choice == "e":
                g.add_exception(i.id)
            elif choice == "d":
                i.source_2 = ""
                i.sutta_2 = ""
                i.example_2 = ""
                g.db_session.commit()
            elif choice == "s":
                i.source_1 = i.source_2
                i.sutta_1 = i.sutta_2
                i.example_1 = i.example_2
                i.source_2 = ""
                i.sutta_2 = ""
                i.example_2 = ""
                g.db_session.commit()
            elif choice == "q":
                g.exit = True

    pr.toc()


if __name__ == "__main__":
    main()
