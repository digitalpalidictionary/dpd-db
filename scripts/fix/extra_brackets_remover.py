#!/usr/bin/env python3

"""
Remove extra brackets in meaning_1
e.g. `goes (to); travels (to)` >> `goes; travels (to)`
"""

import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def test_brackets_list(brackets_list: list[str]) -> bool:
    first_word = ""
    for count, word in enumerate(brackets_list):
        if count == 0:
            first_word = word
            continue
        if word == first_word:
            continue
        else:
            return False
    return True


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    found_count = 0
    for i in db:
        if "(" in i.meaning_1:
            brackets_list = re.findall(r"\(.*?\)", i.meaning_1)
            if len(brackets_list) > 1 and test_brackets_list(brackets_list):
                found_count += 1
                print(found_count)
                print(i.meaning_1)
                print(brackets_list)

                find = re.escape(brackets_list[0])
                subs = len(brackets_list) - 1
                i.meaning_1 = re.sub(
                    f" {find}",
                    "",
                    i.meaning_1,
                    subs,
                )
                print(i.meaning_1)
                print()

    # db_session.commit()


if __name__ == "__main__":
    main()
