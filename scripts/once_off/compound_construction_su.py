#!/usr/bin/env python3

import re

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths as PTH


def main():
    db_session = get_db_session(PTH.dpd_db_path)
    db = db_session.query(PaliWord).all()
    change_list = []

    for i in db:
        if (
            i.pali_1.startswith("su") and
            i.construction.startswith("su + ") and
            not i.compound_type and
            "comp" not in i.grammar and
            "taddhita" not in i.derivative
        ):
            cc1 = re.sub("(su)(.+)", r"\1", i.pali_clean)
            cc2 = re.sub("(su)(.+)", r"\2", i.pali_clean)
            if re.findall(r"^(\w)\1", cc2):
                cc2 = re.sub(r"(\w)\1", r"\1", cc2)
            i.compound_type = "kammadhāraya"
            cc = f"{cc1} + {cc2}"
            print(i.pali_1, cc)
            i.compound_construction = cc
            change_list.append(i.pali_1)

    print(db_search_string(change_list))
    print(len(change_list))
    # db_session.commit()
    db_session.close()


if __name__ == "__main__":
    main()
