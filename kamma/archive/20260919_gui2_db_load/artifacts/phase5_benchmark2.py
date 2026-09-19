"""Test eager-detector cost + fast corpus hydration, with correctness checks.

Production condition: decon cache seeded (cache hit), fresh connections.
"""

import statistics
import time
from typing import Any

from sqlalchemy import select

from db.models import DpdHeadword
from gui2.database_manager import DatabaseManager
from tools.cache_load import (
    load_decon_no_headwords_cache,
    save_decon_no_headwords_cache,
)
from tools.synonym_variant import RelationshipDetector

DB = "/tmp/dpd_load_test.db"
REPS = 3

DEFERS = [
    DpdHeadword.inflections_html,
    DpdHeadword.freq_html,
    DpdHeadword.inflections_sinhala,
    DpdHeadword.inflections_devanagari,
    DpdHeadword.inflections_thai,
]
SKIP = {c.key for c in DEFERS}


def med(fn, n=REPS) -> tuple[float, Any]:
    ts = []
    out = None
    for _ in range(n):
        t0 = time.perf_counter()
        out = fn()
        ts.append(time.perf_counter() - t0)
    return statistics.median(ts), out


def main():
    dbm = DatabaseManager()
    dbm.pth.dpd_db_path = __import__("pathlib").Path(DB)
    dbm.new_db_session()

    # seed the cache (production: cache hit)
    if load_decon_no_headwords_cache(dbm.db_session) is None:
        rows = dbm.db_session.query(DpdHeadword.id).count()  # touch
        del rows
        from db.models import Lookup

        r = (
            dbm.db_session.query(Lookup.lookup_key)
            .filter(Lookup.headwords == "", Lookup.deconstructor != "")
            .all()
        )
        save_decon_no_headwords_cache(dbm.db_session, {i[0] for i in r if i[0]})

    # 1. current initialize_db, as-is (eager detector included)
    def init_current():
        dbm._corpus_stale = True
        dbm.get_all_lemma_1_and_lemma_clean()
        dbm.get_all_pos()
        dbm.get_all_roots()
        dbm.get_all_root_families()
        dbm.get_all_compound_families()
        dbm.get_all_word_families()
        dbm.get_all_patterns()
        dbm.get_all_decon_no_headwords()
        det = RelationshipDetector(dbm.load_corpus())
        return det

    t_current, det_ref = med(init_current)
    print(f"initialize_db as-is (eager detector): {t_current:.3f} s")

    # 2. without the eager detector line
    def init_no_detector():
        dbm._corpus_stale = True
        dbm.get_all_lemma_1_and_lemma_clean()
        dbm.get_all_pos()
        dbm.get_all_roots()
        dbm.get_all_root_families()
        dbm.get_all_compound_families()
        dbm.get_all_word_families()
        dbm.get_all_patterns()
        dbm.get_all_decon_no_headwords()
        dbm.load_corpus()

    t_lazy, _ = med(init_no_detector)
    print(f"initialize_db without eager detector: {t_lazy:.3f} s")
    print(f"  -> eager detector line costs: {t_current - t_lazy:.3f} s")

    # 3. fast hydration: __new__ + __dict__.update
    cols = [c for c in DpdHeadword.__table__.columns if c.name not in SKIP]

    def corpus_fast():
        rows = dbm.db_session.execute(select(*cols)).all()
        out = []
        for row in rows:
            hw = DpdHeadword.__new__(DpdHeadword)
            hw_vars = vars(hw)
            for key, value in row._mapping.items():
                hw_vars[key] = value
            out.append(hw)
        return out

    t_fast, corpus2 = med(corpus_fast)
    print(
        f"fast hydration corpus:                {t_fast:.3f} s  ({len(corpus2)} rows)"
    )

    # current query timing for the same conditions
    def corpus_orm():
        return (
            dbm.db_session.query(DpdHeadword)
            .options(
                __import__("sqlalchemy.orm", fromlist=["defer"]).defer(
                    DpdHeadword.inflections_html
                ),
                __import__("sqlalchemy.orm", fromlist=["defer"]).defer(
                    DpdHeadword.freq_html
                ),
                __import__("sqlalchemy.orm", fromlist=["defer"]).defer(
                    DpdHeadword.inflections_sinhala
                ),
                __import__("sqlalchemy.orm", fromlist=["defer"]).defer(
                    DpdHeadword.inflections_devanagari
                ),
                __import__("sqlalchemy.orm", fromlist=["defer"]).defer(
                    DpdHeadword.inflections_thai
                ),
            )
            .all()
        )

    t_orm, corpus1 = med(corpus_orm)
    print(f"current ORM query corpus:             {t_orm:.3f} s")

    # 4. correctness
    def snapshot(corpus):
        return (
            len(corpus),
            [w.lemma_1 for w in corpus[:200]],
            sum(len(w.inflections_list_all) for w in corpus[:2000]),
            sum(len(w.freq_data_unpack) for w in corpus[:2000]),
            sum(len(w.family_compound_list) for w in corpus[:2000]),
        )

    assert snapshot(corpus1) == snapshot(corpus2), "corpus snapshot differs"
    print("snapshot: identical")

    det_fast = RelationshipDetector(corpus2)
    sample = corpus1[::6000]
    for hw in sample:
        a = det_ref.find_synonyms(hw)
        b = det_fast.find_synonyms(hw)
        assert a == b, f"synonym mismatch for {hw.lemma_1}"
    print(f"find_synonyms on {len(sample)} samples: identical")

    # TSV-style getattr access on fast objects
    for name in ("commentary", "antonym", "compound_type", "root_base", "trans"):
        assert all(hasattr(w, name) for w in corpus2[:100])
    print("TSV-style attribute access: ok")


if __name__ == "__main__":
    main()
