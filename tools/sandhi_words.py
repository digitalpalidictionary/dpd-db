from db.models import Sandhi
from typing import List


def make_sandhi_words_set(sandhi_db: List[Sandhi]) -> set:
    """Input a sandhi_db.
    Returns a list of all sandhi compounds."""

    return set([i.sandhi for i in sandhi_db])


def make_words_in_sandhi_set(sandhi_db: List[Sandhi]) -> set:
    """Input a sandhi_db.
    Returns a list of all words in sandhi compound splits."""

    words_in_sandhi_set = set()
    for i in sandhi_db:
        sandhi_splits = i.split_list
        for sandhi_split in sandhi_splits:
            if ("variant" not in sandhi_split and
                    "spelling" not in sandhi_split):
                for word in sandhi_split.split(" + "):
                    words_in_sandhi_set.add(word)
    return words_in_sandhi_set
