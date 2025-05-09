from collections import defaultdict
from typing import Dict

from sqlalchemy.orm import Session
from unidecode import unidecode

from db.models import DpdHeadword, Lookup
from tools.pali_sort_key import pali_list_sorter


def make_roots_count_dict(db_session: Session) -> Dict[str, int]:
    roots_db = db_session.query(DpdHeadword).all()
    roots_count_dict: Dict[str, int] = dict()
    for i in roots_db:
        if i.root_key is None:
            continue
        if i.root_key in roots_count_dict:
            roots_count_dict[i.root_key] += 1
        else:
            roots_count_dict[i.root_key] = 1

    return roots_count_dict


def make_headwords_clean_set(db_session: Session) -> set[str]:
    """Make a set of Pāḷi headwords and English meanings."""

    # add headwords
    results = db_session.query(DpdHeadword).all()
    headwords_clean_set = set([i.lemma_clean for i in results])

    # add all english meanings
    results = db_session.query(Lookup).filter(Lookup.epd != "").all()
    headwords_clean_set.update([i.lookup_key for i in results])

    return headwords_clean_set


def make_ascii_to_unicode_dict(db_session: Session) -> dict[str, list[str]]:
    """ASCII Key: Unicode Value."""

    results = db_session.query(DpdHeadword).all()
    headwords_clean_set: set[str] = set()
    for i in results:
        headwords_clean_set.add(i.lemma_clean)
        headwords_clean_set.add(i.lemma_2)
    headwords_sorted_list = pali_list_sorter(headwords_clean_set)

    ascii_to_unicode_dict = defaultdict(list)
    for headword in headwords_sorted_list:
        headword_ascii = unidecode(headword)
        if (
            headword_ascii != headword
            and headword not in ascii_to_unicode_dict[headword_ascii]
        ):
            ascii_to_unicode_dict[headword_ascii].append(headword)

    return ascii_to_unicode_dict
