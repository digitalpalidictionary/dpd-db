"""Phase 1 — re-derive per-component timings of DatabaseManager.initialize_db().

Runs against a throwaway copy of the db (/tmp/dpd_load_test.db), never the
live dpd.db. Times each component separately, 3 repetitions, warm cache,
reports medians.
"""

import statistics
import time
from pathlib import Path

from gui2.database_manager import DatabaseManager
from tools.synonym_variant import RelationshipDetector

DB_COPY = Path("/tmp/dpd_load_test.db")
REPS = 3


def timed(fn, label: str, results: dict[str, list[float]]) -> None:
    start = time.perf_counter()
    fn()
    elapsed = time.perf_counter() - start
    results.setdefault(label, []).append(elapsed)
    print(f"  rep {len(results[label])}: {label:<40} {elapsed:6.3f} s", flush=True)


def main() -> None:
    results: dict[str, list[float]] = {}
    dbm = DatabaseManager()
    # point the manager at the throwaway copy
    dbm.pth.dpd_db_path = DB_COPY
    dbm.new_db_session()

    for rep in range(1, REPS + 1):
        print(f"--- rep {rep} ---", flush=True)
        dbm.pre_initialize_gui_data()  # excluded from timings (runs pre-init)
        timed(
            dbm.get_all_lemma_1_and_lemma_clean,
            "get_all_lemma_1_and_lemma_clean",
            results,
        )
        timed(dbm.get_all_pos, "get_all_pos", results)
        timed(dbm.get_all_roots, "get_all_roots", results)
        timed(dbm.get_all_root_families, "get_all_root_families", results)
        timed(dbm.get_all_compound_families, "get_all_compound_families", results)
        timed(dbm.get_all_word_families, "get_all_word_families", results)
        timed(dbm.get_all_patterns, "get_all_patterns", results)
        timed(dbm.get_all_decon_no_headwords, "get_all_decon_no_headwords", results)
        # force a fresh corpus load each rep (warm page cache)
        dbm._corpus_stale = True
        timed(dbm.load_corpus, "load_corpus", results)
        timed(
            lambda: RelationshipDetector(dbm.db),
            "RelationshipDetector(corpus)",
            results,
        )
        timed(lambda: None, "TOTAL initialize_db equivalent (sum)", results)

    print("\n=== medians ===")
    total = 0.0
    for label, times in results.items():
        if label.startswith("TOTAL"):
            continue
        median = statistics.median(times)
        total += median
        print(f"{label:<40} median {median:6.3f} s")
    print(f"{'TOTAL':<40} median {total:6.3f} s")


if __name__ == "__main__":
    main()
