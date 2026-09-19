#!/usr/bin/env python3
"""Rebuild the all_decon_no_headwords DbInfo cache after lookup changes.

Runs near the end of generate_components.py (after the last lookup writer)
so gui2's initialize_db can read the cached deconstruction set instead of
scanning the 1.28M-row lookup table on every launch.
"""

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.cache_load import save_decon_no_headwords_cache
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    pr.yellow_title("rebuilding all_decon_no_headwords cache")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    lookup_result = (
        db_session.query(Lookup.lookup_key)
        .filter(Lookup.headwords == "")
        .filter(Lookup.deconstructor != "")
        .all()
    )
    decon_set: set[str] = {i[0] for i in lookup_result if i[0]}

    save_decon_no_headwords_cache(db_session, decon_set)
    db_session.close()

    pr.yes(f"{len(decon_set)} keys")
    pr.toc()


if __name__ == "__main__":
    main()
