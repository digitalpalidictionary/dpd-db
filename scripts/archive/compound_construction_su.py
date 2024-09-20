#!/usr/bin/env python3

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    change_list = []

    for i in db:
        if (i.lemma_1.startswith("su") and
            i.construction is not None and
            i.construction.startswith("su + ") and
            not i.compound_type and
            "comp" not in i.grammar and
            i.derivative is not None and
            "taddhita" not in i.derivative):

            cc1 = re.sub("(su)(.+)", r"\1", i.lemma_clean)
            cc2 = re.sub("(su)(.+)", r"\2", i.lemma_clean)
            if re.findall(r"^(\w)\1", cc2):
                cc2 = re.sub(r"(\w)\1", r"\1", cc2)
            i.compound_type = "kammadhāraya"
            cc = f"{cc1} + {cc2}"
            print(i.lemma_1, cc)
            i.compound_construction = cc
            change_list.append(i.lemma_1)

    print(db_search_string(change_list))
    print(len(change_list))
    # db_session.commit()
    db_session.close()


if __name__ == "__main__":
    main()
