#!/usr/bin/env python3

"""Test that grammatical terms always come in the last position.

Find groups of numbered homonyms where a (gram) meaning is not the last
numbered entry, then automatically renumber so (gram) comes last.
"""

import re

import pyperclip
from rich import print
from sqlalchemy import or_
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class GlobalVars:
    """Shared state for the (gram) last-position test."""

    pth: ProjectPaths
    db_session: Session

    contains_grammar_set: set[str]
    fix_me_list: list[str]
    fix_me_total: int

    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.contains_grammar_set = set()
        self.fix_me_list = []
        self.fix_me_total = 0


def find_all_lemma_with_gram(g: GlobalVars) -> None:
    """Make a set of all lemma_1 (minus the last digit) which contains (gram)."""

    pr.green_tmr("finding all lemmas with (gram)")

    contains_grammar = (
        g.db_session.query(DpdHeadword)
        .filter(
            or_(
                DpdHeadword.meaning_1.regexp_match(r"^\(gram\)"),
                DpdHeadword.meaning_2.regexp_match(r"^\(gram\)"),
            )
        )
        .filter(DpdHeadword.lemma_1.regexp_match(r"\d"))
        .order_by(DpdHeadword.lemma_1)
        .all()
    )

    for i in contains_grammar:
        truncated_lemma = re.sub(r"\d*$", "", i.lemma_1)
        g.contains_grammar_set.add(truncated_lemma)

    pr.yes(len(g.contains_grammar_set))


def test_last_position(g: GlobalVars) -> None:
    """Find (gram) not in last position."""

    pr.green_tmr("finding (gram) not in last position")
    for truncated_lemma in g.contains_grammar_set:
        headwords = (
            g.db_session.query(DpdHeadword)
            .filter(DpdHeadword.lemma_1.regexp_match(rf"^{truncated_lemma}\d*$"))
            .order_by(DpdHeadword.lemma_1.desc())
            .all()
        )

        current_contains_gram: bool | None = None
        previous_contains_gram: bool | None = None

        for i in headwords:
            previous_contains_gram = current_contains_gram
            current_contains_gram = "(gram)" in i.meaning_combo

            if previous_contains_gram is False and current_contains_gram is True:
                g.fix_me_list.append(truncated_lemma)
                g.fix_me_total += 1

    pr.yes(len(g.fix_me_list))

    pr.green_title(f"found {g.fix_me_total} words with (gram) not in last position.")


def reorder_grammar(g: GlobalVars) -> None:
    """Automatically reorder the words with (gram) to the end."""

    pr.green_title("automatically reorder grammar")

    for fix_me_count, truncated_lemma in enumerate(g.fix_me_list, start=1):
        print()
        print(f"{fix_me_count:>4} / ", end="")
        print(f"{g.fix_me_total:<4}", end="")
        print(f"{truncated_lemma}")
        print()

        headwords = (
            g.db_session.query(DpdHeadword)
            .filter(DpdHeadword.lemma_1.regexp_match(rf"^{truncated_lemma}\d*$"))
            .order_by(DpdHeadword.lemma_1.asc())
            .all()
        )

        digits: list[int] = []
        for h in headwords:
            last_digits = re.sub(truncated_lemma, "", h.lemma_1)
            digits.append(int(last_digits))
            print(h.lemma_1, h.meaning_combo)

        print()
        digits = sorted(digits)

        if max(digits) < 10:
            # reorder with 'x' in last position to avoid unique constraint errors
            for h in headwords:
                if "(gram)" in h.meaning_combo:
                    h.lemma_1 = f"{truncated_lemma}{digits[-1]}x"
                    del digits[-1]
                else:
                    h.lemma_1 = f"{truncated_lemma}{digits[0]}x"
                    del digits[0]

            g.db_session.commit()

            # remove 'x' in last place
            for h in headwords:
                h.lemma_1 = re.sub("x$", "", h.lemma_1)
                print(h.lemma_1, h.meaning_combo)

            g.db_session.commit()

        else:
            print("please re-order manually")

        print()
        pyperclip.copy(f"/^{truncated_lemma}/")
        print("[yellow]q[white]uit or Enter to continue: ", end="")
        choice = input()
        if choice == "q":
            break


def main() -> None:
    """Find and fix (gram) meanings not in last position among numbered homonyms."""
    pr.yellow_title("test for (gram) not in last position")
    g = GlobalVars()
    find_all_lemma_with_gram(g)
    test_last_position(g)
    if g.fix_me_total > 0:
        reorder_grammar(g)


if __name__ == "__main__":
    main()
