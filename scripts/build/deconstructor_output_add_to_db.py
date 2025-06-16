#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Add to the deconstructor output from
https://github.com/digitalpalidictionary/deconstructor_output.git
to the lookup database.

Used for the GitHub action which cannot currently handle the deconstructor program,
or for local use.
"""

import json
from db.db_helpers import get_db_session
from db.models import Lookup

from tools.lookup_is_another_value import is_another_value
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.update_test_add import update_test_add
from tools.configger import config_test


def main():
    pr.tic()
    pr.title("adding deconstructor output to lookup db")

    if not config_test("deconstructor", "use_premade", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pr.green("setting up data")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    lookup_db: list[Lookup] = db_session.query(Lookup).all()

    # top_five_dict contains the top five most likely splits
    # from the deconstruction process
    with open(pth.deconstructor_output_json) as f:
        top_five_dict = json.load(f)

    pr.yes("ok")

    update_set, test_set, add_set = update_test_add(lookup_db, top_five_dict)

    pr.green("updating db")

    # update test add
    update_count = 0
    for i in lookup_db:
        if i.lookup_key in update_set:
            i.deconstructor_pack(top_five_dict[i.lookup_key])
            update_count += 1
        elif i.lookup_key in test_set:
            if is_another_value(i, "deconstructor"):
                i.deconstructor = ""
                update_count += 1
            else:
                db_session.delete(i)
                update_count += 1
    db_session.commit()
    pr.yes(update_count)

    # add
    pr.green("adding to db")
    add_to_db = []
    for constructed, deconstructed in top_five_dict.items():
        if constructed in add_set:
            add_me = Lookup()
            add_me.lookup_key = constructed
            add_me.deconstructor_pack(deconstructed)
            add_to_db.append(add_me)

    db_session.add_all(add_to_db)
    pr.yes(len(add_to_db))

    db_session.commit()
    db_session.close()

    pr.toc()


if __name__ == "__main__":
    main()
