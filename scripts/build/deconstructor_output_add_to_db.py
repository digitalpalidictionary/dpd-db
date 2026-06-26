#!/usr/bin/env python3

"""
Add to the deconstructor output from
https://github.com/digitalpalidictionary/deconstructor_output.git
to the lookup database.

Used for the GitHub action which cannot currently handle the deconstructor program,
or for local use.
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

    if config_read("generate", "deconstructor", "yes") == "no":
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pr.green_tmr("setting up data")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # top_five_dict contains the top five most likely splits
    # from the deconstruction process
    with pth.deconstructor_output_json.open(encoding="utf-8") as f:
        top_five_dict = json.load(f)

    pr.yes("ok")

    pr.green_tmr("syncing deconstructor column")
    result = sync_lookup_column(db_session, "deconstructor", top_five_dict)
    db_session.close()
    pr.yes(result.updated + result.inserted)

    pr.toc()


if __name__ == "__main__":
    main()
