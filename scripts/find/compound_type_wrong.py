#!/usr/bin/env python3

"""Find dupes in id and lemma_1"""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.tic()
    pr.yellow_title("finding all compound types")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword.compound_type).all()

    types = set([i[0] for i in db])
    for i in pali_list_sorter(types):
        print(i)

    pr.toc()


if __name__ == "__main__":
    main()
