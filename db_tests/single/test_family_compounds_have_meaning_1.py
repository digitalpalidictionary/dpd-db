#!/usr/bin/env python3

"""Find family compounds that have no headword entry with a meaning_1.

Builds a set of all family compound names from FamilyCompound table,
then checks DpdHeadword for entries matching each compound name.
Reports compounds with zero headword entries carrying meaning_1.
"""

import json

import pyperclip
from rich import print
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyCompound
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class GlobalVars:
    pth: ProjectPaths
    db_session: Session
    db_fc: list[FamilyCompound]
    db_hw: list[DpdHeadword]
    family_compound_set: set[str]
    no_meaning_dict: dict[str, dict[str, list[str]]]
    exceptions: list[str]
    exit: bool

    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db_fc = self.db_session.query(FamilyCompound).all()
        self.db_hw = self.db_session.query(DpdHeadword).all()
        self.family_compound_set = set()
        self.no_meaning_dict = {}
        self.exceptions = self.load_exceptions()
        self.exit = False

    def load_exceptions(self) -> list[str]:
        if self.pth.family_compounds_meaning_exceptions_path.exists():
            with open(
                self.pth.family_compounds_meaning_exceptions_path, encoding="utf-8"
            ) as f:
                return json.load(f)
        return []

    def save_exceptions(self) -> None:
        with open(
            self.pth.family_compounds_meaning_exceptions_path, "w", encoding="utf-8"
        ) as f:
            json.dump(self.exceptions, f, indent=2)

    def add_exception(self, key: str) -> None:
        self.exceptions.append(key)
        self.save_exceptions()


def make_family_compound_set(g: GlobalVars) -> None:
    """Build a set of all family compound names."""
    for i in g.db_fc:
        g.family_compound_set.add(i.compound_family)


def test_family_compounds_have_meaning_1(g: GlobalVars) -> None:
    """Collect per-compound stats on whether any headword has meaning_1."""

    for i in g.db_hw:
        if i.lemma_clean in g.family_compound_set:
            if i.meaning_1:
                if g.no_meaning_dict.get(i.lemma_clean):
                    g.no_meaning_dict[i.lemma_clean]["yes"].append(i.lemma_1)
                else:
                    g.no_meaning_dict[i.lemma_clean] = {
                        "yes": [i.lemma_1],
                        "no": [],
                    }
            else:
                if g.no_meaning_dict.get(i.lemma_clean):
                    g.no_meaning_dict[i.lemma_clean]["no"].append(i.lemma_1)
                else:
                    g.no_meaning_dict[i.lemma_clean] = {
                        "yes": [],
                        "no": [i.lemma_1],
                    }


def display_missing_meanings(g: GlobalVars) -> None:
    """Display compounds with no meaning_1, one by one."""

    missing = {
        k: v
        for k, v in g.no_meaning_dict.items()
        if not v["yes"] and k not in g.exceptions
    }
    total = len(missing)

    count = 0
    for lemma_clean, data in missing.items():
        if g.exit:
            break
        print()
        print(f"[dark_orange]{count + 1} of {total}")
        print(f"[dark_orange]{'family compound':<20}[/dark_orange][white]{lemma_clean}")
        print(
            f"[dark_orange]{'no meaning_1':<20}[/dark_orange][white]{' '.join(data['no'])}"
        )
        pyperclip.copy(lemma_clean)
        print()
        print(
            "[yellow]e[white]xception [yellow]q[white]uit or Enter for next: ", end=""
        )
        choice = input()
        if choice == "e":
            g.add_exception(lemma_clean)
        elif choice == "q":
            g.exit = True
        count += 1

    pr.summary("total", count)


def main() -> None:
    pr.tic()
    print("[bright_yellow]find family compounds with no meaning_1")
    g = GlobalVars()
    make_family_compound_set(g)
    test_family_compounds_have_meaning_1(g)
    display_missing_meanings(g)
    pr.toc()


if __name__ == "__main__":
    main()
