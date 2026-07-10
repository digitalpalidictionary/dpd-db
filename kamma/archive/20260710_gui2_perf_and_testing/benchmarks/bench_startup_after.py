"""7.5: startup AFTER Phase 7 lazy loading. Constructs the REAL (now-lazy)
ToolKit and measures its eager-init cost + RSS, then forces each deferred
manager to quantify what moved out of startup. Compare against
results/3.2_startup.json (before) and results/3.3_memory.json.

A real flet.Page can't be built standalone, but ToolKit only stores the page
reference during __init__ (UsernameManager/AppBarUpdater keep it, none call
methods on it), so page=None is safe here — same trick bench_startup.py uses.
"""

import time

from bench_common import (
    force_throwaway_db_globally,
    num_fds,
    rss_mb,
    write_result,
)

# Must run before any manager __init__ opens a db session.
force_throwaway_db_globally()


def main() -> None:
    from gui2.toolkit import ToolKit

    def timed(fn):
        start = time.perf_counter()
        result = fn()
        return result, round((time.perf_counter() - start) * 1000, 2)

    rss_before = rss_mb()
    fds_before = num_fds()

    # ToolKit init runs pre_initialize_gui_data, which does a cold-disk full
    # scan on the 2.2 GB throwaway db on first touch. RSS/fds are cache-
    # independent, so measure them here; time is reported both cold (this run)
    # and warm (a second pre_init below) so the eager number isn't page-cache
    # noise (see the Phase 3 variance note).
    tk, cold_init_ms = timed(lambda: ToolKit(None))  # type: ignore[arg-type]
    rss_after_eager = rss_mb()
    fds_after_eager = num_fds()

    # Warm pre_init reflects the 7.4 DISTINCT change without cold-cache noise.
    _, warm_preinit_ms = timed(tk.db_manager.pre_initialize_gui_data)

    deferred: dict[str, float] = {}
    rss_progression: dict[str, float] = {"after_eager_init": round(rss_after_eager, 1)}

    def force(attr: str) -> None:
        _, ms = timed(lambda: getattr(tk, attr))
        deferred[attr] = ms
        rss_progression[f"after_{attr}"] = round(rss_mb(), 1)

    for attr in (
        "ai_manager",
        "wordfinder_manager",
        "bold_definitions_search_manager",
        "additions_manager",
        "corrections_manager",
        "ai_search_popup",
        "wordfinder_popup",
    ):
        force(attr)

    total_deferred = round(sum(deferred.values()), 2)
    rss_after_all = rss_mb()

    result = {
        "cold_init_ms": cold_init_ms,
        "warm_preinit_ms": warm_preinit_ms,
        "baseline_preinit_ms": 347.19,
        "total_deferred_ms": total_deferred,
        "deferred_ms_desc": dict(sorted(deferred.items(), key=lambda kv: -kv[1])),
        "rss_before_mb": round(rss_before, 1),
        "rss_after_eager_init_mb": round(rss_after_eager, 1),
        "eager_rss_delta_mb": round(rss_after_eager - rss_before, 1),
        "rss_after_forcing_all_mb": round(rss_after_all, 1),
        "deferred_rss_delta_mb": round(rss_after_all - rss_after_eager, 1),
        "fds_before": fds_before,
        "fds_after_eager_init": fds_after_eager,
        "fds_after_forcing_all": num_fds(),
        "rss_progression_mb": rss_progression,
    }

    print(f"\ncold ToolKit init: {cold_init_ms:.1f} ms (cold-cache, incl. pre_init)")
    print(f"warm pre_init: {warm_preinit_ms:.1f} ms (was 347 ms baseline)")
    print(f"total deferred out of startup: {total_deferred:.1f} ms")
    print(f"{'deferred manager':<45} {'ms':>10}")
    for label, ms in result["deferred_ms_desc"].items():  # type: ignore[union-attr]
        print(f"{label:<45} {ms:>10.2f}")
    print(
        f"\neager RSS delta: {result['eager_rss_delta_mb']} MB; "
        f"deferred RSS delta: {result['deferred_rss_delta_mb']} MB"
    )

    write_result("7.5_startup_after", result)


if __name__ == "__main__":
    main()
