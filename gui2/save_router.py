# -*- coding: utf-8 -*-
"""The one place that decides where a headword save goes.

User 1 writes the db. A contributor writes only their own JSON files, so a
shared db is never changed by a contributor session."""

from typing import TYPE_CHECKING

from db.models import DpdHeadword

if TYPE_CHECKING:
    from gui2.toolkit import ToolKit


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
            toolkit.corrections_manager.update_corrections(word, comment)
        else:
            additions.add_additions(word, comment)
    except OSError as e:
        return False, str(e)
    return True, ""
