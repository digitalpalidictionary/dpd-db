"""3.3: memory RSS at key points, plus an engine-leak probe: call
new_db_session() N times with vs without closing the previous session,
measuring RSS growth and open-fd growth in each case.
"""

from bench_common import force_throwaway_db_globally, num_fds, rss_mb, write_result
from sqlalchemy import text

from gui2.database_manager import DatabaseManager

# Must run before any DatabaseManager method is CALLED (not before import —
# Python resolves module-global names lazily at call time via __globals__,
# so patching after import but before use is sufficient).
force_throwaway_db_globally()

N = 50


def _touch(session) -> None:
    """SQLAlchemy engines/sessions are lazy — no real connection opens until
    a query runs. Real GUI usage always queries right after new_db_session(),
    so force that here for a representative measurement."""
    session.execute(text("SELECT 1"))


def main() -> None:
    baseline_rss = rss_mb()
    baseline_fds = num_fds()

    db = DatabaseManager()
    after_construct_rss = rss_mb()
    after_construct_fds = num_fds()

    db.initialize_db()
    after_corpus_load_rss = rss_mb()
    after_corpus_load_fds = num_fds()

    # --- engine-leak probe: WITHOUT closing previous session ---
    rss_series_no_close = []
    for _ in range(N):
        db.new_db_session()
        _touch(db.db_session)
        rss_series_no_close.append(rss_mb())
    fds_after_no_close = num_fds()

    # Rebuild for a clean second probe
    db2 = DatabaseManager()

    # --- engine-leak probe: WITH closing previous session first ---
    rss_series_with_close = []
    for _ in range(N):
        db2.db_session.close()
        db2.new_db_session()
        _touch(db2.db_session)
        rss_series_with_close.append(rss_mb())
    fds_after_with_close = num_fds()

    result = {
        "baseline_rss_mb": round(baseline_rss, 1),
        "baseline_fds": baseline_fds,
        "after_construct_rss_mb": round(after_construct_rss, 1),
        "after_construct_fds": after_construct_fds,
        "after_corpus_load_rss_mb": round(after_corpus_load_rss, 1),
        "after_corpus_load_fds": after_corpus_load_fds,
        "corpus_load_rss_delta_mb": round(
            after_corpus_load_rss - after_construct_rss, 1
        ),
        f"new_db_session_x{N}_no_close": {
            "rss_before_mb": round(after_corpus_load_rss, 1),
            "rss_after_mb": round(rss_series_no_close[-1], 1),
            "rss_delta_mb": round(rss_series_no_close[-1] - after_corpus_load_rss, 1),
            "fds_before": after_corpus_load_fds,
            "fds_after": fds_after_no_close,
            "fds_delta": fds_after_no_close - after_corpus_load_fds,
        },
        f"new_db_session_x{N}_with_close": {
            "rss_before_mb": round(rss_series_with_close[0], 1),
            "rss_after_mb": round(rss_series_with_close[-1], 1),
            "rss_delta_mb": round(
                rss_series_with_close[-1] - rss_series_with_close[0], 1
            ),
            "fds_before": after_corpus_load_fds,  # db2 just constructed, comparable baseline
            "fds_after": fds_after_with_close,
            "fds_delta": fds_after_with_close - after_corpus_load_fds,
        },
    }

    print(f"baseline: {baseline_rss:.1f} MB, {baseline_fds} fds")
    print(
        f"after DatabaseManager(): {after_construct_rss:.1f} MB, {after_construct_fds} fds"
    )
    print(
        f"after initialize_db() (~83k rows): {after_corpus_load_rss:.1f} MB "
        f"(+{after_corpus_load_rss - after_construct_rss:.1f} MB), {after_corpus_load_fds} fds"
    )
    print(
        f"\n{N}x new_db_session() WITHOUT close: "
        f"{rss_series_no_close[-1] - after_corpus_load_rss:+.1f} MB, "
        f"fds {after_corpus_load_fds} -> {fds_after_no_close} "
        f"({fds_after_no_close - after_corpus_load_fds:+d})"
    )
    print(
        f"{N}x new_db_session() WITH close: "
        f"{rss_series_with_close[-1] - rss_series_with_close[0]:+.1f} MB, "
        f"fds -> delta {fds_after_with_close - after_corpus_load_fds:+d} "
        f"(from a fresh DatabaseManager() baseline)"
    )

    write_result("3.3_memory", result)


if __name__ == "__main__":
    main()
