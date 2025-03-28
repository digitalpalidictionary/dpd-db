#!/usr/bin/env python3


from sqlalchemy.orm.session import Session

from db.models import DpdHeadword
from tools.clean_machine import clean_machine
from tools.printer import printer as pr


class GlobalVars:
    headword: DpdHeadword
    columns: list[str] = ["example_1", "example_2", "commentary"]
    column: str
    text: str
    all_words_set: set[str] = set()


def cleanup_text_and_add_to_set(g: GlobalVars) -> list:
    """Clean up the text in the column and add to all_words_set"""
    g.text = getattr(g.headword, g.column)
    if g.text:
        # remove bold tags
        g.text = g.text.replace("<b>", "").replace("</b>", "")

        # clean, but keep the hyphens
        g.text = clean_machine(g.text, remove_hyphen=False)

        # replace hyphens with spaces
        g.text = g.text.replace("-", " ")

        # add to set
        g.all_words_set = g.all_words_set | set(g.text.split())


def make_all_words_in_dpd_set(db_session: Session) -> set[str]:
    """Return a set of all words in dpd_headwords table,
    from example_1, example_2 and commentary columns,
    with all hyphenations as separate words.

    Why? So that
    1. the components of hyphenated words
    2. words from outside the canon
    can be recognized by the deconstructor.
    """

    pr.green("making set of all words in dpd")
    db = db_session.query(DpdHeadword).all()
    g = GlobalVars()
    for counter, g.headword in enumerate(db):
        for g.column in g.columns:
            cleanup_text_and_add_to_set(g)
    pr.yes(len(g.all_words_set))
    return g.all_words_set
