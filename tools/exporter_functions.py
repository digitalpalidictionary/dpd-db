from sqlalchemy.orm import object_session

from typing import List
from typing import Optional
from typing import Set

from db.models import PaliWord
from db.models import FamilyCompound
from db.models import FamilySet


from db.get_db_session import get_db_session
from tools.paths import ProjectPaths

pth = ProjectPaths()

_cached_cf_set: Optional[Set[str]] = None

def cf_set_gen() -> Set[str]:
    """generate a list of all compounds families"""
    global _cached_cf_set

    if _cached_cf_set is not None:
        return _cached_cf_set

    db_session = get_db_session(pth.dpd_db_path)
    cf_db = db_session.query(FamilyCompound).all()

    cf_set: Set[str] = set()
    for i in cf_db:
        cf_set.add(i.compound_family)

    _cached_cf_set = cf_set
    return cf_set


def get_family_compounds(i: PaliWord) -> List[FamilyCompound]:
    db_session = object_session(i)
    if db_session is None:
        raise Exception("No db_session")

    if i.family_compound:
        fc = db_session.query(
            FamilyCompound
        ).filter(
            FamilyCompound.compound_family.in_(i.family_compound_list),
        ).all()

        # sort by order of the  family compound list
        word_order = i.family_compound_list
        fc = sorted(fc, key=lambda x: word_order.index(x.compound_family))

    else:
        fc = db_session.query(
            FamilyCompound
        ).filter(
            FamilyCompound.compound_family == i.pali_clean
        ).all()

    # Make sure it's not a lazy-loaded iterable.
    fc = list(fc)

    return fc

def get_family_set(i: PaliWord) -> List[FamilySet]:
    db_session = object_session(i)
    if db_session is None:
        raise Exception("No db_session")

    fs = db_session.query(
        FamilySet
    ).filter(
        FamilySet.set.in_(i.family_set_list)
    ).all()

    # sort by order of the  family set list
    word_order = i.family_set_list
    fs = sorted(fs, key=lambda x: word_order.index(x.set))

    # Make sure it's not a lazy-loaded iterable.
    fs = list(fs)

    return fs
