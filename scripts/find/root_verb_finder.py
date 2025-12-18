#!/usr/bin/env python3

"""Find all verbs related to a root"""

from collections import defaultdict
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from rich import print


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    root_family = input("What root family are you looking for?: ")
    db = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.family_root == root_family)
        .all()
    )

    root_family_dict = defaultdict(set)
    pos_ignore_list = ["adj", "masc", "nt", "fem", "ind"]

    for i in db:
        if i.pos not in pos_ignore_list and i.neg not in ["neg", "negx2"]:
            root_family_dict[i.pos].add(i.lemma_clean)

    for pos, words in root_family_dict.items():
        print(f"{pos:<10}", end=" ")
        print(f"{', '.join([word for word in words])}")


if __name__ == "__main__":
    main()
