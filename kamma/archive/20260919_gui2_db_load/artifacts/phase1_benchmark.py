"""Phase 1 — benchmark candidate mechanisms on the throwaway db copy.

(a) deconstructor set: current ORM query vs core select vs pickled cache read
(b) corpus: current Query+defer vs execute(select(...)) vs raw core projection
Every variant is checked for identical output against the current code.
"""

import pickle
import statistics
import time
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import defer

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup

DB_COPY = Path("/tmp/dpd_load_test.db")
REPS = 3

DEFERS = [
    defer(DpdHeadword.inflections_html),
    defer(DpdHeadword.freq_html),
    defer(DpdHeadword.inflections_sinhala),
    defer(DpdHeadword.inflections_devanagari),
    defer(DpdHeadword.inflections_thai),
]


def timed(fn: Callable[[], object], results: dict[str, list[float]]) -> object:
    start = time.perf_counter()
    out = fn()
    results.setdefault(label_of(fn), []).append(time.perf_counter() - start)
    return out


_LABELS: dict[int, str] = {}


def label_of(fn: Callable[[], object]) -> str:
    for fn_id, name in _LABELS.items():
        if id(fn) == fn_id:
            return name
    return getattr(fn, "__name__", "unknown")


def run(name: str, fn: Callable[[], object], results: dict[str, list[float]]) -> object:
    _LABELS[id(fn)] = name
    return timed(fn, results)


def main() -> None:
    session = get_db_session(DB_COPY)
    results: dict[str, list[float]] = {}

    # ---- (a) deconstructor set ----
    def decon_orm() -> set[str]:
        rows = (
            session.query(Lookup.lookup_key)
            .filter(Lookup.headwords == "")
            .filter(Lookup.deconstructor != "")
            .all()
        )
        return {i[0] for i in rows if i[0]}

    def decon_core() -> set[str]:
        rows = session.execute(
            select(Lookup.lookup_key)
            .where(Lookup.headwords == "")
            .where(Lookup.deconstructor != "")
        ).all()
        return {r[0] for r in rows if r[0]}

    reference_set = decon_orm()
    print(f"decon set size: {len(reference_set)}")

    blob = pickle.dumps(reference_set, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"pickle blob: {len(blob) / 1e6:.1f} MB")

    def decon_pickle() -> set[str]:
        out: set[str] = pickle.loads(blob)
        return out

    run("decon current ORM query", decon_orm, results)
    run("decon core select", decon_core, results)
    run("decon pickle.loads cache", decon_pickle, results)
    assert decon_core() == reference_set, "core select set differs"
    assert decon_pickle() == reference_set, "pickle set differs"

    # ---- (b) corpus ----
    def corpus_current() -> list[DpdHeadword]:
        return session.query(DpdHeadword).options(*DEFERS).all()

    def corpus_execute() -> list[DpdHeadword]:
        return list(
            session.execute(select(DpdHeadword).options(*DEFERS)).scalars().all()
        )

    skip_cols = {
        "inflections_html",
        "freq_html",
        "inflections_sinhala",
        "inflections_devanagari",
        "inflections_thai",
    }
    cols = [c for c in DpdHeadword.__table__.columns if c.name not in skip_cols]

    def corpus_raw() -> list[DpdHeadword]:
        rows = session.execute(select(*cols)).all()
        return [DpdHeadword(**row._mapping) for row in rows]

    ref_corpus = corpus_current()
    print(f"corpus size: {len(ref_corpus)}")

    def snapshot(corpus: list[DpdHeadword]) -> object:
        return (
            len(corpus),
            [w.lemma_1 for w in corpus[:100]],
            sum(len(w.inflections_list_all) for w in corpus[:1000]),
            sum(len(w.freq_data_unpack) for w in corpus[:1000]),
        )

    run("corpus current query+defer", corpus_current, results)
    run("corpus execute(select)+defer", corpus_execute, results)
    run("corpus raw core projection", corpus_raw, results)
    assert snapshot(corpus_execute()) == snapshot(ref_corpus), "execute corpus differs"
    assert snapshot(corpus_raw()) == snapshot(ref_corpus), "raw corpus differs"

    session.close()
    print("\n=== medians ===")
    for name_, times in results.items():
        print(f"{name_:<32} median {statistics.median(times):6.3f} s")


if __name__ == "__main__":
    main()
