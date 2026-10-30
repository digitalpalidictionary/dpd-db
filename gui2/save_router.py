# -*- coding: utf-8 -*-
"""The one place that decides where a headword save goes.

User 1 writes the db. A contributor writes only their own JSON files, so a
shared db is never changed by a contributor session."""

from typing import TYPE_CHECKING

from db.models import DpdHeadword

if TYPE_CHECKING:
    from gui2.toolkit import ToolKit


def changed_columns(db_row: DpdHeadword | None, word: DpdHeadword) -> list[str]:
    """The columns whose value in word differs from the db row. None and ""
    count as the same, and so do values that differ only by the stray spaces
    make_dpd_headword_from_dict removes: an untouched field is not a change."""
    if db_row is None:
        return []

    def text(value: object) -> str:
        return "" if value is None else str(value).strip().replace("  ", " ")

    # Only the columns the form supplied: the form never sets the dates, the
    # inflection tables or the frequency data, and the db row always holds them.
    supplied = vars(word)
    return [
        column.name
        for column in DpdHeadword.__table__.columns
        if column.name in supplied
        and text(getattr(word, column.name, None))
        != text(getattr(db_row, column.name, None))
    ]


def save_headword(
    toolkit: "ToolKit", word: DpdHeadword, comment: str, is_existing: bool
) -> tuple[bool, str]:
    """Save a word. Returns (committed, error message)."""
    if not toolkit.username_manager.is_not_primary():
        if is_existing:
            return toolkit.db_manager.update_word_in_db(word)
        committed, message = toolkit.db_manager.add_word_to_db(word)
        return committed, str(message)

    additions = toolkit.additions_manager
    try:
        # An own addition stays an addition when re-edited. Any other existing
        # id is a db word, so the edit is a correction.
        if is_existing and additions.is_not_in_additions(word.id):
            # The db row is read without the overlay, so a re-edit of an own
            # correction still compares with the db, not the earlier edit.
            db_row = toolkit.db_manager.db_session.get(DpdHeadword, word.id)
            toolkit.corrections_manager.update_corrections(
                word, comment, changed_columns(db_row, word)
            )
        else:
            additions.add_additions(word, comment)
    except OSError as e:
        return False, str(e)
    return True, ""
