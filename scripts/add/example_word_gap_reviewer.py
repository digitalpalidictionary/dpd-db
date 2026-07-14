"""Interactively review words in example_1 and example_2 that are
missing from the lookup table, missing meaning_1, or missing an example.
Each hit is printed with context and copied to the clipboard; press
Enter to move to the next one.

Set ROUTE below to choose what to look for:
  1 — word doesn't exist in the lookup table at all
  2 — word's headword(s) are missing meaning_1
  3 — word's headword(s) are missing meaning_1 and example_1 (default)
"""

import re
from dataclasses import dataclass, field

import pyperclip
from rich import print
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.clean_machine import clean_machine
from tools.paths import ProjectPaths
from tools.printer import printer as pr

ROUTE: int = 3


@dataclass
class ReviewState:
    db_session: Session
    route: int = ROUTE
    lookup: Lookup | None = field(default=None, init=False)
    text: str = field(default="", init=False)


def make_clean_word_list(
    state: ReviewState, headword: DpdHeadword, column: str
) -> list[str]:
    """Clean up the text in one column and return a list of words."""
    text = getattr(headword, column)
    text = re.sub(r"\(.*?\)", "", text)  # remove word in brackets
    text = text.replace("<b>", "").replace("</b>", "")
    text = clean_machine(text)
    text = text.replace("-", " ")
    state.text = text
    return text.split()


def check_in_lookup(state: ReviewState, word: str) -> None:
    state.lookup = state.db_session.query(Lookup).filter_by(lookup_key=word).first()


def print_result(
    state: ReviewState, headword: DpdHeadword, column: str, word: str
) -> None:
    print(f"[cyan]{headword.id}")
    print(f"[cyan]{headword.lemma_1}")
    print(f"[cyan]{column}")
    if column == "example_1":
        print(headword.source_1, headword.sutta_1)
    elif column == "example_2":
        print(headword.source_2, headword.sutta_2)
    text_highlight = state.text.replace(word, f"[cyan]{word}[/cyan]")
    print(f"[green]{text_highlight}")
    print(f"[cyan]{word}")
    pyperclip.copy(word)
    input()


def find_missing_meaning_1(
    state: ReviewState, headword: DpdHeadword, column: str, word: str
) -> None:
    """Print the word if none of its headwords have meaning_1."""
    if state.lookup is None:
        return
    dpd_ids = state.lookup.headwords_unpack
    if not dpd_ids:
        return
    needs_meaning_1 = all(
        not (hw := state.db_session.query(DpdHeadword).filter_by(id=dpd_id).first())
        or not hw.meaning_1
        for dpd_id in dpd_ids
    )
    if needs_meaning_1:
        print_result(state, headword, column, word)


def find_missing_example(
    state: ReviewState, headword: DpdHeadword, column: str, word: str
) -> None:
    """Print the word if none of its headwords have both meaning_1 and example_1."""
    if state.lookup is None:
        return
    dpd_ids = state.lookup.headwords_unpack
    if not dpd_ids:
        return
    needs_example = all(
        not (hw := state.db_session.query(DpdHeadword).filter_by(id=dpd_id).first())
        or not (hw.meaning_1 and hw.example_1)
        for dpd_id in dpd_ids
    )
    if needs_example:
        print_result(state, headword, column, word)


def check_word(
    state: ReviewState, headword: DpdHeadword, column: str, word: str
) -> None:
    check_in_lookup(state, word)
    if state.lookup is None:
        if state.route == 1:
            print_result(state, headword, column, word)
    elif state.route == 2:
        find_missing_meaning_1(state, headword, column, word)
    elif state.route == 3:
        find_missing_example(state, headword, column, word)


_ROUTE_DESCRIPTIONS = {
    1: "words in example_1/example_2 that don't exist in the lookup table at all",
    2: "words whose headword(s) are missing meaning_1",
    3: "words whose headword(s) are missing meaning_1 and example_1",
}


def main() -> None:
    pr.yellow_title("example word gap reviewer")
    pr.white(
        f"route {ROUTE}: scanning example_1/example_2 for "
        f"{_ROUTE_DESCRIPTIONS[ROUTE]}\n"
        "each hit shows its context and copies the word to the clipboard — "
        "press Enter to see the next one, Ctrl-C to stop"
    )
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    state = ReviewState(db_session=db_session)

    headwords: list[DpdHeadword] = db_session.query(DpdHeadword).all()
    for headword in headwords:
        for column in ("example_1", "example_2"):
            for word in make_clean_word_list(state, headword, column):
                check_word(state, headword, column, word)


if __name__ == "__main__":
    main()
