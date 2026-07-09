#!/usr/bin/env python3

"""
Sync deconstructor_output.json into lookup.deconstructor.

Reads go_modules/deconstructor/output/deconstructor_output.json (produced by
go_modules/deconstructor/main.go) and upserts via tools/lookup_sync.py.
Used in CI release workflows and local generate_components.py.
"""

import json
from db.db_helpers import get_db_session

from tools.lookup_sync import sync_lookup_column
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.configger import config_read


def main() -> None:
    pr.tic()
    pr.yellow_title("adding deconstructor output to lookup db")

    if config_read("generate", "deconstructor", "yes") != "yes":
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pr.green_tmr("setting up data")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # top_five_dict contains the top five most likely splits
    # from the deconstruction process
    with pth.go_deconstructor_output_json.open(encoding="utf-8") as f:
        top_five_dict = json.load(f)

    pr.yes("ok")

    pr.green_tmr("syncing deconstructor column")
    result = sync_lookup_column(
        db_session, "deconstructor", top_five_dict, use_raw_sql=True
    )
    db_session.close()
    pr.yes(result.updated + result.inserted)

    pr.toc()


if __name__ == "__main__":
    main()
