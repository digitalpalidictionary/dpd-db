from typing import Optional, Set

from db.get_db_session import get_db_session
from db.models import FamilyCompound

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