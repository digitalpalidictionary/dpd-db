"""Interactively review words in example_1 and example_2 that are
missing from the lookup table, missing meaning_1, or missing an example.
Each hit is printed with context and copied to the clipboard.

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

_ROUTE_DESCRIPTIONS = {
    1: "words in example_1/example_2 that don't exist in the lookup table at all",
    2: "words whose headword(s) are missing meaning_1",
    3: "words whose headword(s) are missing meaning_1 and example_1",
}


@dataclass
class ReviewState:
    db_session: Session
    route: int = ROUTE
    lookup: Lookup | None = field(default=None, init=False)
    text: str = field(default="", init=False)
    hit_count: int = field(default=0, init=False)


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
    """Show one flagged word: which headword's example it came from,
    the source citation, the sentence with the word highlighted, and
    copy the word to the clipboard ready to paste into gui2."""
    state.hit_count += 1
    if column == "example_1":
        source, sutta = headword.source_1, headword.sutta_1
    else:
        source, sutta = headword.source_2, headword.sutta_2

    print()
    print(f"[bold white]#{state.hit_count}  found in {headword.lemma_1!r}'s {column}")
    print(f"[dim]{source} {sutta}")
    text_highlight = state.text.replace(
        word, f"[bold cyan on black]{word}[/bold cyan on black]"
    )
    print(f"  {text_highlight}")
    print(f"[bold cyan]-> {word}[/bold cyan]  [dim](copied to clipboard)")
    pyperclip.copy(word)
    if input("(q)uit or Enter for next ").strip().lower() == "q":
        raise SystemExit


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


def main() -> None:
    pr.yellow_title("example word gap reviewer")
    pr.white(
        f"route {ROUTE}: scanning example_1/example_2 for "
        f"{_ROUTE_DESCRIPTIONS[ROUTE]}\n"
        "each hit shows its context and copies the word to the clipboard"
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
