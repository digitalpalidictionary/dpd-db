"""3.4: microbenchmark db.db_helpers.get_db_session() called N times fresh
(current behavior: new Engine every call) vs a cached-engine prototype that
reuses one Engine and just makes a new Session bound to it.
"""

import time

from bench_common import THROWAWAY_DB, num_fds, rss_mb, write_result
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from db.db_helpers import get_db_session

N = 200


def current_behavior(n: int) -> dict:
    fds_before = num_fds()
    rss_before = rss_mb()
    start = time.perf_counter()
    for _ in range(n):
        session = get_db_session(THROWAWAY_DB)
        session.execute(text("SELECT 1"))
        session.close()
    elapsed_ms = (time.perf_counter() - start) * 1000
    return {
        "total_ms": round(elapsed_ms, 2),
        "per_call_ms": round(elapsed_ms / n, 3),
        "fds_delta": num_fds() - fds_before,
        "rss_delta_mb": round(rss_mb() - rss_before, 1),
    }


def cached_engine_prototype(n: int) -> dict:
    fds_before = num_fds()
    rss_before = rss_mb()

    engine = create_engine(
        f"sqlite+pysqlite:///{THROWAWAY_DB}",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_wal_mode(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")

    session_factory = sessionmaker(bind=engine)

    start = time.perf_counter()
    for _ in range(n):
        session = session_factory()
        session.execute(text("SELECT 1"))
        session.close()
    elapsed_ms = (time.perf_counter() - start) * 1000
    engine.dispose()
    return {
        "total_ms": round(elapsed_ms, 2),
        "per_call_ms": round(elapsed_ms / n, 3),
        "fds_delta": num_fds() - fds_before,
        "rss_delta_mb": round(rss_mb() - rss_before, 1),
    }


def main() -> None:
    current = current_behavior(N)
    cached = cached_engine_prototype(N)

    speedup = (
        round(current["per_call_ms"] / cached["per_call_ms"], 1)
        if cached["per_call_ms"] > 0
        else None
    )

    print(f"N = {N} session-open-query-close cycles\n")
    print(f"current (new Engine every call):   {current}")
    print(f"cached-engine prototype:            {cached}")
    print(f"\nper-call speedup (cached vs current): {speedup}x")
    print(
        f"fd growth: current={current['fds_delta']:+d}  cached={cached['fds_delta']:+d}"
    )

    write_result(
        "3.4_engine_cost",
        {
            "n": N,
            "current_new_engine_every_call": current,
            "cached_engine_prototype": cached,
            "per_call_speedup_x": speedup,
        },
    )


if __name__ == "__main__":
    main()
