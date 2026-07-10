"""3.6: corpus load timing — initialize_db(), make_inflections_lists(),
make_pass2_lists() each do a fresh .all() of the ~83k headword table, plus
RelationshipDetector construction time.

6.4 re-run: after the Phase 6 corpus cache, make_inflections_lists() and
make_pass2_lists() derive from the one cached load; extra sections time the
cached load_corpus() (tests-tab path) and a stale reload after a write.
"""

import time

from bench_common import force_throwaway_db_globally, write_result
from gui2.database_manager import DatabaseManager
from tools.synonym_variant import RelationshipDetector

# Must run before any DatabaseManager method is CALLED (not before import —
# Python resolves module-global names lazily at call time via __globals__,
# so patching after import but before use is sufficient).
force_throwaway_db_globally()


def timed(fn) -> float:
    start = time.perf_counter()
    fn()
    return (time.perf_counter() - start) * 1000


def main() -> None:
    db = DatabaseManager()

    initialize_db_ms = timed(db.initialize_db)
    row_count = len(db.db)

    make_inflections_ms = timed(db.make_inflections_lists)
    make_pass2_ms = timed(db.make_pass2_lists)

    detector_ms = timed(lambda: RelationshipDetector(db.db))

    # tests-tab path: cached corpus, no query
    cached_load_corpus_ms = timed(db.load_corpus)

    # after a write: stale reload + re-derive
    db.mark_corpus_stale()
    stale_make_inflections_ms = timed(db.make_inflections_lists)

    result = {
        "row_count": row_count,
        "initialize_db_ms": round(initialize_db_ms, 2),
        "make_inflections_lists_ms": round(make_inflections_ms, 2),
        "make_pass2_lists_ms": round(make_pass2_ms, 2),
        "relationship_detector_build_ms": round(detector_ms, 2),
        "cached_load_corpus_ms": round(cached_load_corpus_ms, 2),
        "stale_reload_make_inflections_ms": round(stale_make_inflections_ms, 2),
        "total_first_three_calls_ms": round(
            initialize_db_ms + make_inflections_ms + make_pass2_ms, 2
        ),
    }

    print(f"row_count: {row_count}")
    print(
        f"initialize_db():          {initialize_db_ms:9.2f} ms  (the one full .all())"
    )
    print(f"make_inflections_lists(): {make_inflections_ms:9.2f} ms  (derive only)")
    print(f"make_pass2_lists():       {make_pass2_ms:9.2f} ms  (derive only)")
    print(f"RelationshipDetector():   {detector_ms:9.2f} ms")
    print(f"load_corpus() cached:     {cached_load_corpus_ms:9.2f} ms  (tests tab)")
    print(
        f"stale reload + derive:    {stale_make_inflections_ms:9.2f} ms  (after a write)"
    )
    print(
        f"\nTotal initialize_db + both derives: "
        f"{result['total_first_three_calls_ms']:.1f} ms"
    )

    write_result("6.4_corpus_after", result)


if __name__ == "__main__":
    main()
