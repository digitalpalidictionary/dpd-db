from typing import List
from db.models import PaliWord


def make_clean_headwords_set(dpd_db: List[PaliWord]) -> set:
    """A set of clean headwords in the dictionary."""
    all_headwords_clean: set = set()
    for counter, i in enumerate(dpd_db):
        all_headwords_clean.add(i.pali_clean)

    return all_headwords_clean
