"""A few helpful lists and functions for the exporter."""

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths as PTH

EXCLUDE_FROM_SETS: set = {
    "dps", "ncped", "pass1", "sandhi"}

EXCLUDE_FROM_FREQ: set = {
    "abbrev", "cs", "idiom", "letter", "prefix", "root", "suffix", "ve"}

_cached_cf_set = None


def cf_set_gen():
    """generate a list of all compounds families"""
    global _cached_cf_set

    if _cached_cf_set is not None:
        return _cached_cf_set

    db_session = get_db_session(PTH.dpd_db_path)
    cf_db = db_session.query(
        PaliWord
    ).filter(PaliWord.family_compound != ""
             ).all()

    cf_set = set()
    for i in cf_db:
        cfs = i.family_compound.split(" ")
        for cf in cfs:
            cf_set.add(cf)

    _cached_cf_set = cf_set
    return cf_set


CF_SET: set = cf_set_gen()


def make_roots_count_dict(DB_SESSION):
    roots_db = DB_SESSION.query(PaliWord).all()
    roots_count_dict = {}
    for i in roots_db:
        if i.root_key in roots_count_dict:
            roots_count_dict[i.root_key] += 1
        else:
            roots_count_dict[i.root_key] = 1

    return roots_count_dict
