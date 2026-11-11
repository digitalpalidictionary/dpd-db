"""F3 probe: time and peak memory of the after-save detector rebuild, full vs
slim row load. Run each variant in a fresh process:
    PYTHONPATH=. uv run python /tmp/dpd_20261111_scratch/detector_probe.py full
    PYTHONPATH=. uv run python /tmp/dpd_20261111_scratch/detector_probe.py slim
Read-only on dpd.db. A watchdog thread kills the process (os._exit(3)) above
1,500 MB RSS so it can never starve the laptop."""

import os
import resource
import sys
import threading
import time


def _watchdog() -> None:
    import psutil

    proc = psutil.Process()
    while True:
        rss_mb = proc.memory_info().rss / 1024 / 1024
        if rss_mb > 1500:
            print(f"CAPPED: rss {rss_mb:.0f} MB over 1500 MB")
            os._exit(3)
        time.sleep(0.5)


def main() -> None:
    variant = sys.argv[1]
    threading.Thread(target=_watchdog, daemon=True).start()

    from sqlalchemy.orm import defer, load_only

    from db.db_helpers import get_db_session
    from db.models import DpdHeadword
    from gui2.database_manager import CONTRIBUTOR_CORPUS_COLUMNS
    from tools.paths import ProjectPaths
    from tools.synonym_variant import RelationshipDetector

    t0 = time.perf_counter()
    session = get_db_session(ProjectPaths().dpd_db_path)
    query = session.query(DpdHeadword)
    if variant == "full":
        # exactly the query in _detector_rebuild_worker
        rows = query.options(
            defer(DpdHeadword.inflections_html),
            defer(DpdHeadword.freq_html),
            defer(DpdHeadword.inflections_sinhala),
            defer(DpdHeadword.inflections_devanagari),
            defer(DpdHeadword.inflections_thai),
        ).all()
    else:
        # the way _load_contributor_corpus loads, on this private session
        columns = [getattr(DpdHeadword, name) for name in CONTRIBUTOR_CORPUS_COLUMNS]
        with_meaning = query.filter(
            DpdHeadword.meaning_1 != ""
        ).options(load_only(*columns)).all()
        without_meaning = (
            query.filter(DpdHeadword.meaning_1 == "")
            .options(load_only(*columns, DpdHeadword.freq_data))
            .all()
        )
        rows = with_meaning + without_meaning
    load_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    RelationshipDetector(rows)
    build_s = time.perf_counter() - t1

    session.close()
    peak_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"{variant} load {load_s:.2f} s build {build_s:.2f} s peak {peak_kb / 1024:.0f} MB")


if __name__ == "__main__":
    main()
