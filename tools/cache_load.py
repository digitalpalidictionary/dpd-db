#!/usr/bin/env python3

"""Get cf_set and idioms_set from the DbInfo cache."""

import csv
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
        sutta_info_cache: set[str] = {i[0] for i in db}
        for _, dpd_sutta_var in db:
            if dpd_sutta_var:
                for alias in dpd_sutta_var.split(";"):
                    alias = alias.strip()
                    if alias:
                        sutta_info_cache.add(alias)
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


def _read_audio_index() -> list[tuple[str, bool, bool, bool]]:
    """Parse the audio index TSV.

    Raises FileNotFoundError if the TSV is missing — run
    audio/index_release_download.py (CI) or audio/db_release_download.py
    (local) to fetch it.
    """
    tsv_path = pth.dpd_audio_index_tsv_path
    if not tsv_path.exists():
        raise FileNotFoundError(
            f"Audio index TSV not found at {tsv_path}. "
            "Run audio/index_release_download.py (or audio/db_release_download.py) to fetch it."
        )

    rows: list[tuple[str, bool, bool, bool]] = []
    with open(tsv_path, "r", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # header
        for lemma_clean, has_male1, has_male2, has_female1 in reader:
            rows.append(
                (
                    lemma_clean,
                    has_male1 == "1",
                    has_male2 == "1",
                    has_female1 == "1",
                )
            )
    return rows


@lru_cache(maxsize=1)
def load_audio_set() -> frozenset[str]:
    """generate a set of all audio headwords"""
    return frozenset(
        lemma_clean for lemma_clean, m1, m2, f1 in _read_audio_index() if m1 or m2 or f1
    )


@lru_cache(maxsize=1)
def load_audio_dict() -> dict[str, tuple[bool, bool, bool]]:
    """generate a dict of audio headwords with voice availability (male1, male2, female1)"""
    return {
        lemma_clean: (m1, m2, f1) for lemma_clean, m1, m2, f1 in _read_audio_index()
    }


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
