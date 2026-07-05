#!/usr/bin/env python3

"""Count how many words pass2pre will surface in each Aṅguttara Nikāya book.

Replicates the gui2 Pass2Pre discovery filter (the `missing_examples_dict` that
drives the GUI's "Remaining" counter) per nipāta, without the interactive
matching step, and reports only the counts.
"""

import json
from pathlib import Path

from sqlalchemy.orm import Session, defer

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from gui2.needs_example import is_missing_sutta_example
from gui2.pass2_pre_file_manager import Pass2PreFileManager
from gui2.paths import Gui2Paths
from gui2.spelling import SpellingMistakesFileManager
from gui2.variants import VariantReadingFileManager
from tools.clean_machine import clean_machine
from tools.cst_sc_text_sets import make_cst_text_list
from tools.paths import ProjectPaths
from tools.printer import printer as pr

AN_BOOKS: list[str] = [
    "an1",
    "an2",
    "an3",
    "an4",
    "an5",
    "an6",
    "an7",
    "an8",
    "an9",
    "an10",
    "an11",
]


def build_db_sets(db_session: Session) -> tuple[set[str], set[str]]:
    """Reproduce make_pass2_lists + get_all_decon_no_headwords from gui2."""

    headwords: list[DpdHeadword] = (
        db_session.query(DpdHeadword)
        .options(
            defer(DpdHeadword.inflections_html),
            defer(DpdHeadword.freq_html),
            defer(DpdHeadword.inflections_sinhala),
            defer(DpdHeadword.inflections_devanagari),
            defer(DpdHeadword.inflections_thai),
            defer(DpdHeadword.freq_data),
        )
        .all()
    )

    missing_example: set[str] = set()
    for i in headwords:
        if is_missing_sutta_example(i):
            missing_example.update(i.inflections_list_all)

    decon_rows = (
        db_session.query(Lookup.lookup_key)
        .filter(Lookup.headwords == "")
        .filter(Lookup.deconstructor != "")
        .all()
    )
    decon_no_headwords: set[str] = {row[0] for row in decon_rows if row[0]}

    return missing_example, decon_no_headwords


def sc_words_for_book(sc_book_dir: Path) -> set[str]:
    """Reproduce SuttaCentralSource word extraction for one nipāta folder."""

    words: set[str] = set()
    if not sc_book_dir.is_dir():
        return words
    for file_path in sc_book_dir.rglob("*"):
        if not file_path.is_file():
            continue
        data: dict[str, str] = json.load(file_path.open(encoding="utf-8"))
        for sentence in data.values():
            pali = clean_machine(sentence.replace("ṁ", "ṃ").lower())
            words.update(pali.split())
    return words


def main() -> None:
    pr.tic()
    pr.yellow_title("pass2pre surfacing counts — aṅguttara nikāya")

    pth = ProjectPaths()
    gui2pth = Gui2Paths()
    db_session = get_db_session(pth.dpd_db_path)

    pr.green_tmr("building db sets")
    missing_example, decon_no_headwords = build_db_sets(db_session)
    pr.yes(str(len(missing_example)))

    variants = VariantReadingFileManager().variants_dict
    spelling = SpellingMistakesFileManager().spelling_mistakes_dict
    file_manager = Pass2PreFileManager("an", gui2pth)

    def is_missing_example(word: str) -> bool:
        return (
            (word in missing_example or word in decon_no_headwords)
            and word not in variants
            and word not in spelling
            and word not in file_manager.unmatched
            and word not in file_manager.matched
        )

    sc_an_dir = pth.sc_data_dir / "sutta" / "an"

    all_surfaced: set[str] = set()
    counts: dict[str, int] = {}
    for book in AN_BOOKS:
        pr.green_tmr(f"counting {book}")
        cst_words = set(
            make_cst_text_list(
                [book],
                niggahita="ṃ",
                dedupe=True,
                add_hyphenated_parts=True,
                show_errors=False,
            )
        )
        sc_words = sc_words_for_book(sc_an_dir / book)
        surfaced = {w for w in (cst_words | sc_words) if is_missing_example(w)}
        counts[book] = len(surfaced)
        all_surfaced.update(surfaced)
        pr.yes(str(len(surfaced)))

    pr.green_title("words pass2pre will surface per book")
    for book in AN_BOOKS:
        pr.summary(book, str(counts[book]))
    pr.summary("total (sum)", str(sum(counts.values())))
    pr.summary("total (unique)", str(len(all_surfaced)))

    pr.toc()


if __name__ == "__main__":
    main()
