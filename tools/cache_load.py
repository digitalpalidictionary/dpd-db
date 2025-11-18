#!/usr/bin/env python3

"""Get cf_set and idioms_set from the DbInfo cache."""

import json

from db.db_helpers import get_db_session
from tools.paths import ProjectPaths

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

_cf_set_cache = None
_idioms_set_cache = None
_sutta_info_cache = None


def load_sutta_info_set():
    from db.models import SuttaInfo

    global _sutta_info_cache

    if _sutta_info_cache is not None:
        return _sutta_info_cache
    else:
        db = (
            db_session.query(SuttaInfo.dpd_sutta, SuttaInfo.dpd_sutta_var)
            .filter(SuttaInfo.dpd_code != "")
            .all()
        )
        _sutta_info_cache = set([i[0] for i in db])
        # _sutta_info_cache.update([i[1] for i in db if i[1]]) exclude for now
        return _sutta_info_cache


def load_cf_set() -> set[str]:
    """generate a list of all compounds families"""
    from db.models import DbInfo

    global _cf_set_cache

    if _cf_set_cache is not None:
        return _cf_set_cache
    else:
        cf_set_cache = db_session.query(DbInfo).filter_by(key="cf_set").first()
        cf_set = json.loads(cf_set_cache.value)
        _cf_set_cache = cf_set
        return cf_set


def load_idioms_set() -> set[str]:
    """generate a list of all compounds families"""
    from db.models import DbInfo

    global _idioms_set_cache

    if _idioms_set_cache is not None:
        return _idioms_set_cache
    else:
        idioms_set_cache = db_session.query(DbInfo).filter_by(key="idioms_set").first()
        idioms_set = json.loads(idioms_set_cache.value)
        _idioms_set_cache = idioms_set
        return idioms_set


if __name__ == "__main__":
    from db.models import DbInfo

    print(load_cf_set(DbInfo))


# --------------------------------------old-----------------
# pth = ProjectPaths()

# _cached_cf_set: Optional[Set[str]] = None

# def cf_set_gen() -> Set[str]:
#     """generate a list of all compounds families"""
#     global _cached_cf_set

#     if _cached_cf_set is not None:
#         return _cached_cf_set

#     db_session = get_db_session(pth.dpd_db_path)
#     cf_db = db_session.query(FamilyCompound).all()

#     cf_set: Set[str] = set()
#     for i in cf_db:
#         cf_set.add(i.compound_family)

#     _cached_cf_set = cf_set
#     return cf_set
