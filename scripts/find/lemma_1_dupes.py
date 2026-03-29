#!/usr/bin/env python3

"""Find dupes in id and lemma_1"""

from collections import Counter
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.tic()
    pr.yellow_title("finding dupes in lemma_1")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword.lemma_1).all()

    counter = Counter(i[0] for i in db)

    for word, count in counter.items():
        if count == 2:
            print(word)

    pr.toc()


if __name__ == "__main__":
    main()
