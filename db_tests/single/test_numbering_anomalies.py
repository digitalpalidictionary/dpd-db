#!/usr/bin/env python3

"""Find anomalies in headword numbering.

Checks four categories:
- Numbered lemmas where the same lemma_clean has different root_key across entries
- Dotted-number lemmas where the same base has different root_key
- Numbered compounds where the same lemma_clean has different family_compound
- Dotted-number compounds where the same base has different family_compound
"""

import json
import re

import pyperclip
from rich import print
from sqlalchemy.orm import Session

from db.models import DpdHeadword
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class GlobalVars:
    pth: ProjectPaths
    db_session: Session
    db: list[DpdHeadword]
    exceptions: list[str]
    exit: bool

    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.db_session.query(DpdHeadword).all()
        self.exceptions = self.load_exceptions()
        self.exit = False

    def load_exceptions(self) -> list[str]:
        if self.pth.numbering_anomalies_exceptions_path.exists():
            with open(
                self.pth.numbering_anomalies_exceptions_path, encoding="utf-8"
            ) as f:
                return json.load(f)
        return []

    def save_exceptions(self) -> None:
        with open(
            self.pth.numbering_anomalies_exceptions_path, "w", encoding="utf-8"
        ) as f:
            json.dump(self.exceptions, f, indent=2)

    def add_exception(self, key: str) -> None:
        self.exceptions.append(key)
        self.save_exceptions()


def main() -> None:
    pr.tic()
    print("[bright_yellow]finding numbering anomalies")
    g = GlobalVars()
    root_numbering(g)
    root_numbering_dot(g)
    compound_numbering(g)
    compound_numbering_dot(g)
    pr.toc()


def prompt(g: GlobalVars, key: str) -> int:
    """Show prompt and handle choice. Returns 1 if counted, 0 if excepted."""
    print(
        "[yellow]e[white]xception [yellow]q[white]uit or Enter for next: ",
        end="",
    )
    choice = input()
    if choice == "e":
        g.add_exception(key)
        return 0
    elif choice == "q":
        g.exit = True
    return 1


def root_numbering(g: GlobalVars) -> None:
    """Check numbered lemmas (no dot) for inconsistent root_key."""
    if g.exit:
        return
    hw_rt_dict: dict[str, str] = {}
    counter = 0

    for i in g.db:
        if (
            re.findall(r"\d", i.lemma_1)
            and "." not in i.lemma_1
            and i.lemma_clean not in g.exceptions
        ):
            if i.lemma_clean not in hw_rt_dict:
                hw_rt_dict[i.lemma_clean] = i.root_key or ""
            elif hw_rt_dict[i.lemma_clean] != i.root_key:
                print(f"[magenta1]{i.lemma_clean}")
                print(f"[green]  root 1: {hw_rt_dict[i.lemma_clean]}")
                print(f"[green]  root 2: {i.root_key}")
                print()
                pyperclip.copy(rf"/^{i.lemma_clean} \d/")
                counter += prompt(g, i.lemma_clean)
                if g.exit:
                    break

    pr.summary("root numbering", counter)


def root_numbering_dot(g: GlobalVars) -> None:
    """Check dotted-number lemmas for inconsistent root_key."""
    if g.exit:
        return
    hw_rt_dict: dict[str, str] = {}
    counter = 0

    for i in g.db:
        if re.findall(r"\d", i.lemma_1) and "." in i.lemma_1:
            first_number = re.sub(r"\..+", "", i.lemma_1)
            if first_number not in g.exceptions:
                if first_number not in hw_rt_dict:
                    hw_rt_dict[first_number] = i.root_key or ""
                elif hw_rt_dict[first_number] != i.root_key:
                    print(f"[magenta1]{first_number}")
                    print(f"[green]  root 1: {hw_rt_dict[first_number]}")
                    print(f"[green]  root 2: {i.root_key}")
                    print()
                    pyperclip.copy(rf"/^{i.lemma_clean} /")
                    counter += prompt(g, first_number)
                    if g.exit:
                        break

    pr.summary("root num. dot", counter)


def compound_numbering(g: GlobalVars) -> None:
    """Check numbered compound lemmas for inconsistent family_compound."""
    if g.exit:
        return
    compound_exceptions = ["koṭṭhāsa"]
    hw_cnstr_dict: dict[str, str] = {}
    counter = 0

    for i in g.db:
        if (
            i.lemma_clean not in compound_exceptions
            and i.lemma_clean not in g.exceptions
            and re.findall(r"\d", i.lemma_1)
            and "." not in i.lemma_1
            and re.findall(r"\bcomp\b", i.grammar)
            and i.meaning_1
        ):
            if i.lemma_clean not in hw_cnstr_dict:
                hw_cnstr_dict[i.lemma_clean] = i.family_compound or ""
            elif hw_cnstr_dict[i.lemma_clean] != i.family_compound:
                print(f"[magenta1]{i.lemma_clean}")
                print(f"[green]  family compound 1: {hw_cnstr_dict[i.lemma_clean]}")
                print(f"[green]  family compound 2: {i.family_compound}")
                print()
                pyperclip.copy(rf"/^{i.lemma_clean} \d/")
                counter += prompt(g, i.lemma_clean)
                if g.exit:
                    break

    pr.summary("compound numb.", counter)


def compound_numbering_dot(g: GlobalVars) -> None:
    """Check dotted-number compound lemmas for inconsistent family_compound."""
    if g.exit:
        return
    hw_cnstr_dict: dict[str, str] = {}
    counter = 0

    for i in g.db:
        if (
            re.findall(r"\d", i.lemma_1)
            and "." in i.lemma_1
            and re.findall(r"\bcomp\b", i.grammar)
            and i.meaning_1
        ):
            first_number = re.sub(r"\..+", "", i.lemma_1)
            if first_number not in g.exceptions:
                if first_number not in hw_cnstr_dict:
                    hw_cnstr_dict[first_number] = i.family_compound or ""
                elif hw_cnstr_dict[first_number] != i.family_compound:
                    print(f"[magenta1]{first_number}")
                    print(f"[green]  family compound 1: {hw_cnstr_dict[first_number]}")
                    print(f"[green]  family compound 2: {i.family_compound}")
                    print()
                    pyperclip.copy(rf"/^{i.lemma_clean} /")
                    counter += prompt(g, first_number)
                    if g.exit:
                        break

    pr.summary("comp. numb. dot", counter)


if __name__ == "__main__":
    main()
