"""Returns a set of headwords without numbers from the DpdHeadwords table."""

from typing import List
from db.models import DpdHeadwords


def make_clean_headwords_set(dpd_db: List[DpdHeadwords]) -> set:
    """A set of clean headwords in the dictionary."""
    all_headwords_clean: set = set()
    for counter, i in enumerate(dpd_db):
        all_headwords_clean.add(i.lemma_clean)

    return all_headwords_clean
