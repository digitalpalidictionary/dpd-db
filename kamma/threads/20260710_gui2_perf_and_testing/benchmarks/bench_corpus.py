"""3.6: corpus load timing — initialize_db(), make_inflections_lists(),
make_pass2_lists() each do a fresh .all() of the ~83k headword table, plus
RelationshipDetector construction time.
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

    result = {
        "row_count": row_count,
        "initialize_db_ms": round(initialize_db_ms, 2),
        "make_inflections_lists_ms": round(make_inflections_ms, 2),
        "make_pass2_lists_ms": round(make_pass2_ms, 2),
        "relationship_detector_build_ms": round(detector_ms, 2),
        "total_redundant_full_table_loads_ms": round(
            initialize_db_ms + make_inflections_ms + make_pass2_ms, 2
        ),
    }

    print(f"row_count: {row_count}")
    print(
        f"initialize_db():          {initialize_db_ms:9.2f} ms  (includes a full .all())"
    )
    print(f"make_inflections_lists(): {make_inflections_ms:9.2f} ms  (2nd full .all())")
    print(f"make_pass2_lists():       {make_pass2_ms:9.2f} ms  (3rd full .all())")
    print(f"RelationshipDetector():   {detector_ms:9.2f} ms")
    print(
        f"\nTotal cost of 3 separate full-table loads that could be 1: "
        f"{result['total_redundant_full_table_loads_ms']:.1f} ms"
    )

    write_result("3.6_corpus", result)


if __name__ == "__main__":
    main()
