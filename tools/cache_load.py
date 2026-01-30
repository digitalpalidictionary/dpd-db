#!/usr/bin/env python3

"""Get cf_set and idioms_set from the DbInfo cache."""

import json

from db.db_helpers import get_db_session
from tools.paths import ProjectPaths

pth = ProjectPaths()


_cf_set_cache = None
_idioms_set_cache = None
_sutta_info_cache = None
_audio_set_cache = None
_audio_dict_cache = None
_tpr_codes_set_cache = None


def load_sutta_info_set():
    from db.models import SuttaInfo

    global _sutta_info_cache

    if _sutta_info_cache is not None:
        return _sutta_info_cache
    else:
        with get_db_session(pth.dpd_db_path) as db_session:
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
        with get_db_session(pth.dpd_db_path) as db_session:
            cf_set_cache = db_session.query(DbInfo).filter_by(key="cf_set").first()
            if cf_set_cache:
                cf_set = json.loads(cf_set_cache.value)
                _cf_set_cache = cf_set
                return cf_set
            return set()


def load_idioms_set() -> set[str]:
    """generate a list of all compounds families"""
    from db.models import DbInfo

    global _idioms_set_cache

    if _idioms_set_cache is not None:
        return _idioms_set_cache
    else:
        with get_db_session(pth.dpd_db_path) as db_session:
            idioms_set_cache = (
                db_session.query(DbInfo).filter_by(key="idioms_set").first()
            )
            if idioms_set_cache:
                idioms_set = json.loads(idioms_set_cache.value)
                _idioms_set_cache = idioms_set
                return idioms_set
            return set()


def load_audio_set() -> set[str]:
    """generate a set of all audio headwords"""
    from sqlalchemy import or_

    from audio.db.db_helpers import get_audio_session
    from audio.db.models import DpdAudio

    global _audio_set_cache

    if _audio_set_cache is not None:
        return _audio_set_cache
    else:
        audio_session = get_audio_session()
        try:
            results = (
                audio_session.query(DpdAudio.lemma_clean)
                .filter(
                    or_(
                        DpdAudio.male1.isnot(None),
                        DpdAudio.male2.isnot(None),
                        DpdAudio.female1.isnot(None),
                    )
                )
                .distinct()
                .all()
            )
            _audio_set_cache = {r[0] for r in results}
            return _audio_set_cache
        finally:
            audio_session.close()


def load_audio_dict() -> dict[str, tuple[bool, bool, bool]]:
    """generate a dict of audio headwords with voice availability (male1, male2, female1)"""
    from audio.db.db_helpers import get_audio_session
    from audio.db.models import DpdAudio

    global _audio_dict_cache

    if _audio_dict_cache is not None:
        return _audio_dict_cache
    else:
        audio_session = get_audio_session()
        try:
            results = audio_session.query(
                DpdAudio.lemma_clean,
                (DpdAudio.male1.isnot(None)),
                (DpdAudio.male2.isnot(None)),
                (DpdAudio.female1.isnot(None)),
            ).all()

            _audio_dict_cache = {
                r[0]: (
                    r[1],
                    r[2],
                    r[3],
                )
                for r in results
            }
            return _audio_dict_cache
        finally:
            audio_session.close()


def load_tpr_codes_set() -> set[str]:
    """load TPR sutta codes from json file"""
    global _tpr_codes_set_cache

    if _tpr_codes_set_cache is not None:
        return _tpr_codes_set_cache
    else:
        if pth.tpr_codes_json_path.exists():
            with open(pth.tpr_codes_json_path, "r", encoding="utf-8") as f:
                _tpr_codes_set_cache = set(json.load(f))
                return _tpr_codes_set_cache
        return set()


if __name__ == "__main__":
    print(load_cf_set())


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
