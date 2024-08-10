
#!/usr/bin/env python3

"""Get cf_set and idioms_set from the DbInfo cache."""

import json
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

_cf_set_cache = None
_idioms_set_cache = None


def load_cf_set() -> set[str]:
    """generate a list of all compounds families"""
    from db.models import DbInfo 
    global _cf_set_cache

    if _cf_set_cache is not None:
        return _cf_set_cache
    else:
        cf_set_cache = db_session \
            .query(DbInfo) \
            .filter_by(key="cf_set") \
                .first()
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
        idioms_set_cache = db_session \
            .query(DbInfo) \
            .filter_by(key="idioms_set") \
            .first()
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
