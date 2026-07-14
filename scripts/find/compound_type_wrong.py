#!/usr/bin/env python3

"""Print every distinct compound_type value in the db, Pāḷi-sorted,
to eyeball wrong or malformed compound types."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    pr.yellow_title("finding all compound types")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword.compound_type).all()

    types = {i[0] for i in db}
    for compound_type in pali_list_sorter(types):
        print(compound_type)

    pr.toc()


if __name__ == "__main__":
    main()
