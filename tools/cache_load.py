#!/usr/bin/env python3

"""Get cf_set and idioms_set from the DbInfo cache."""

import json
from functools import lru_cache

from db.db_helpers import get_db_session
from tools.paths import ProjectPaths

pth = ProjectPaths()


@lru_cache(maxsize=1)
def load_sutta_info_set() -> frozenset[str]:
    from db.models import SuttaInfo

    with get_db_session(pth.dpd_db_path) as db_session:
        db = (
            db_session.query(SuttaInfo.dpd_sutta, SuttaInfo.dpd_sutta_var)
            .filter(SuttaInfo.dpd_code != "")
            .all()
        )
        sutta_info_cache = set([i[0] for i in db])
        # sutta_info_cache.update([i[1] for i in db if i[1]]) exclude for now
        return frozenset(sutta_info_cache)


@lru_cache(maxsize=1)
def load_cf_set() -> frozenset[str]:
    """generate a list of all compounds families"""
    from db.models import DbInfo

    with get_db_session(pth.dpd_db_path) as db_session:
        cf_set_cache = db_session.query(DbInfo).filter_by(key="cf_set").first()
        if cf_set_cache:
            cf_list = json.loads(cf_set_cache.value)
            return frozenset(cf_list)
        return frozenset()


@lru_cache(maxsize=1)
def load_idioms_set() -> frozenset[str]:
    """generate a list of all compounds families"""
    from db.models import DbInfo

    with get_db_session(pth.dpd_db_path) as db_session:
        idioms_set_cache = db_session.query(DbInfo).filter_by(key="idioms_set").first()
        if idioms_set_cache:
            idioms_list = json.loads(idioms_set_cache.value)
            return frozenset(idioms_list)
        return frozenset()


@lru_cache(maxsize=1)
def load_audio_set() -> frozenset[str]:
    """generate a set of all audio headwords"""
    from sqlalchemy import or_

    from audio.db.db_helpers import get_audio_session
    from audio.db.models import DpdAudio

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
        audio_set_cache = {r[0] for r in results}
        return frozenset(audio_set_cache)
    finally:
        audio_session.close()


@lru_cache(maxsize=1)
def load_audio_dict() -> dict[str, tuple[bool, bool, bool]]:
    """generate a dict of audio headwords with voice availability (male1, male2, female1)"""
    from audio.db.db_helpers import get_audio_session
    from audio.db.models import DpdAudio

    audio_session = get_audio_session()
    try:
        results = audio_session.query(
            DpdAudio.lemma_clean,
            (DpdAudio.male1.isnot(None)),
            (DpdAudio.male2.isnot(None)),
            (DpdAudio.female1.isnot(None)),
        ).all()

        audio_dict_cache = {
            r[0]: (
                r[1],
                r[2],
                r[3],
            )
            for r in results
        }
        return audio_dict_cache
    finally:
        audio_session.close()


@lru_cache(maxsize=1)
def load_tpr_codes_set() -> frozenset[str]:
    """load TPR sutta codes from json file"""
    json_path = pth.tpr_codes_json_path
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            tpr_codes_list = json.load(f)
            return frozenset(tpr_codes_list)
    return frozenset()


if __name__ == "__main__":
    print(load_cf_set())
