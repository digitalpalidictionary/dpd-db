#!/usr/bin/env python3

"""Check if lemma_1 and lemma_2 are nearly identical, and if stem matches pattern.

Runs multiple diff-tolerance tests and stem-pattern checks, then presents
each flagged entry one-by-one for review or exception.
"""

import difflib
import json
import re

import pyperclip
from rich import print
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.pos import INDECLINABLES
from tools.printer import printer as pr

POS_DIFFERS = ["masc", "nt", "prefix", "card", "cs", "letter", "root", "suffix", "ve"]


class GlobalVars:
    pth: ProjectPaths
    db_session: Session
    db: list[DpdHeadword]
    exceptions: list[int]
    exit: bool

    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.db_session.query(DpdHeadword).all()
        self.exceptions = self.load_exceptions()
        self.exit = False

    def load_exceptions(self) -> list[int]:
        if self.pth.pali_difference_exceptions_path.exists():
            with open(self.pth.pali_difference_exceptions_path, encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_exceptions(self) -> None:
        with open(self.pth.pali_difference_exceptions_path, "w", encoding="utf-8") as f:
            json.dump(self.exceptions, f, indent=2)

    def add_exception(self, id_: int) -> None:
        self.exceptions.append(id_)
        self.save_exceptions()


def main() -> None:
    pr.tic()
    print("[bright_yellow]find differences in lemma_1, lemma_2, stem pattern")
    g = GlobalVars()

    matches: dict[int, DpdHeadword] = {}
    for i in g.db:
        if i.id in g.exceptions:
            continue
        if (
            test_zero(i)
            or test_one(i)
            or test_two(i)
            or test_three(i)
            or test_stem_pattern(i)
        ):
            matches[i.id] = i

    counter = 0
    for i in matches.values():
        if g.exit:
            break
        print_entry(i)
        pyperclip.copy(i.lemma_1)
        counter += prompt(g, i.id)
        if g.exit:
            break

    pr.summary("total", counter)
    pr.toc()


def prompt(g: GlobalVars, id_: int) -> int:
    """Show prompt and handle choice. Returns 1 if counted."""
    print(
        "[yellow]e[white]xception or Enter for next: ",
        end="",
    )
    choice = input()
    if choice == "e":
        g.add_exception(id_)
    elif choice == "q":
        g.exit = True
    return 1


def print_entry(i: DpdHeadword) -> None:
    """Print entry details in a formatted block."""
    print()
    print(f"[dark_orange]{'id':<12}[/dark_orange][white]{i.id}")
    print(f"[dark_orange]{'lemma_1':<12}[/dark_orange][white]{i.lemma_1}")
    print(f"[dark_orange]{'lemma_2':<12}[/dark_orange][white]{i.lemma_2}")
    print(f"[dark_orange]{'stem':<12}[/dark_orange][white]{i.stem}")
    print(f"[dark_orange]{'pattern':<12}[/dark_orange][white]{i.pattern}")


def compare_strings(str1: str, str2: str, diff: int) -> bool:
    """Return True if the strings differ by at most `diff` characters."""
    sm = difflib.SequenceMatcher(None, str1, str2)
    matching_chars = sm.ratio() * len(str1)
    return len(str1) - matching_chars <= diff


def test_zero(i: DpdHeadword) -> bool:
    """Exact match check for most entries."""
    if i.pos not in POS_DIFFERS and i.meaning_1 and not i.lemma_clean.endswith("ar"):
        return not compare_strings(i.lemma_clean, i.lemma_2, 0)
    return False


def test_one(i: DpdHeadword) -> bool:
    """1-char tolerance for most entries."""
    if (
        not i.lemma_clean.endswith("ant")
        and not i.lemma_clean.endswith("ar")
        and not i.lemma_clean.endswith("as")
    ):
        return not compare_strings(i.lemma_clean, i.lemma_2, 1)
    return False


def test_two(i: DpdHeadword) -> bool:
    """2-char tolerance for -ar/-as stems."""
    if i.lemma_clean.endswith("ar") or i.lemma_clean.endswith("as"):
        return not compare_strings(i.lemma_clean, i.lemma_2, 2)
    return False


def test_three(i: DpdHeadword) -> bool:
    """3-char tolerance for -ant stems."""
    if i.lemma_clean.endswith("ant"):
        return not compare_strings(i.lemma_clean, i.lemma_2, 3)
    return False


def test_stem_pattern(i: DpdHeadword) -> bool:
    """Check if stem + pattern prefix matches lemma_clean."""
    if (
        "*" not in i.stem
        and "!" not in i.stem
        and "-" not in i.stem
        and i.pos not in INDECLINABLES
        and " pl" not in i.pattern
    ):
        pattern = re.sub(" .*$", "", i.pattern)
        pattern = pattern.replace("aī", "a")
        pattern = re.sub(r"\d$", "", pattern)
        stem_pattern = f"{i.stem}{pattern}"
        return not compare_strings(i.lemma_clean, stem_pattern, 0)
    return False


if __name__ == "__main__":
    main()
