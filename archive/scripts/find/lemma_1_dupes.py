#!/usr/bin/env python3

"""Find duplicate lemma_1 values in dpd_headwords."""

from collections import Counter

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    """Print every lemma_1 value that occurs more than once."""
    pr.tic()
    pr.yellow_title("finding dupes in lemma_1")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword.lemma_1).all()

    counter = Counter(i[0] for i in db)

    for word, count in counter.items():
        if count > 1:
            print(word)

    pr.toc()


if __name__ == "__main__":
    main()
