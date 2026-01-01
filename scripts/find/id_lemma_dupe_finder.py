#!/usr/bin/env python3

"""Find dupes in id and lemma_1"""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.tic()
    pr.title("finding dupes in id and lemma1")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    lemma_1_set = set()
    id_set = set()

    for counter, i in enumerate(db):
        if i.lemma_1 not in lemma_1_set:
            lemma_1_set.add(i.lemma_1)
        else:
            pr.error(f"!!! DUPE !!! {i.lemma_1}")

        if i.id not in id_set:
            id_set.add(i.id)
        else:
            pr.error(f"!!! DUPE !!! {i.id}")
    print(f"lemma_1 {len(lemma_1_set)}")
    print(f"id      {len(id_set)}")

    pr.toc()


if __name__ == "__main__":
    main()
