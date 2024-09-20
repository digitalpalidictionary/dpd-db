"""Returns a set of headwords without numbers from the DpdHeadword table."""

from typing import List
from db.models import DpdHeadword


def make_clean_headwords_set(dpd_db: List[DpdHeadword]) -> set:
    """A set of clean headwords in the dictionary."""
    all_headwords_clean: set = set()
    for i in dpd_db:
        all_headwords_clean.add(i.lemma_clean)

    return all_headwords_clean
