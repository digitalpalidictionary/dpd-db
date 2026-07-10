"""Shared helpers for gui2 Phase 3 benchmarks. Not test code — throwaway
scripts for the #157 gui2 perf/testability kamma thread."""

import json
import time
from pathlib import Path

THROWAWAY_DB = Path(
    "/tmp/claude-1000/-home-bodhirasa-MyFiles-3-Active-dpd-db/"
    "c939c391-1055-4576-acca-ae2da27d8474/scratchpad/gui2_bench/dpd_throwaway.db"
)
RESULTS_DIR = Path(__file__).parent / "results"


def timeit(fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, elapsed_ms


def write_result(name: str, data: dict) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"wrote {path}")


def rss_mb() -> float:
    import psutil

    return psutil.Process().memory_info().rss / (1024 * 1024)


def num_fds() -> int:
    import psutil

    return psutil.Process().num_fds()


def force_throwaway_db_globally() -> None:
    """Monkeypatch every known `get_db_session` binding so ANY caller
    (DatabaseManager, BoldDefinitionsSearchManager, etc.) opens the throwaway
    db copy instead of the real 2.2GB dpd.db, no matter what path they pass.

    `from db.db_helpers import get_db_session` copies the function reference
    into the importing module's namespace at import time, so patching
    `db.db_helpers.get_db_session` alone does NOT affect modules that already
    did that import — each such module must be patched individually too.
    Call this FIRST, before importing/constructing anything that might open
    a session, to guarantee we never touch the real production db file.
    """
    import db.db_helpers as db_helpers

    real_get_db_session = db_helpers.get_db_session

    def patched_get_db_session(db_path):
        return real_get_db_session(THROWAWAY_DB)

    db_helpers.get_db_session = patched_get_db_session

    import gui2.database_manager as database_manager

    database_manager.get_db_session = patched_get_db_session

    import tools.bold_definitions_search as bold_definitions_search

    bold_definitions_search.get_db_session = patched_get_db_session
