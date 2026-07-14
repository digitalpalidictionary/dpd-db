#!/usr/bin/env python3

"""Test example_1, example_2 and commentary columns of dpd_headwords for the
pattern '-x-x' (hyphen, consonant, hyphen, same consonant) — a recurring typo
class. Report only; fix hits via gui2, not by auto-replace."""

import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr

CONSONANTS = "kgcjñṭḍṇṅtdnpbmyrlvshḷ"
PATTERN = re.compile(rf"-([{CONSONANTS}])-\1", re.IGNORECASE)
TAG_PATTERN = re.compile(
    rf"-([{CONSONANTS}])(</?b>)-\1",
    re.IGNORECASE,
)

COLUMNS = ("example_1", "example_2", "commentary")


def main() -> None:
    pr.tic()
    pr.yellow_title("find double-consonant typos (-x-x)")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    pr.green_tmr("db query")
    db = db_session.query(DpdHeadword).all()
    pr.yes(str(len(db)))

    pr.green_title("find errors")
    error_count = 0
    for i in db:
        for column in COLUMNS:
            field: str | None = getattr(i, column)
            if not field:
                continue
            if PATTERN.search(field) or TAG_PATTERN.search(field):
                pr.red(f"{i.id} {i.lemma_1} {column}: {field}")
                error_count += 1

    pr.summary("errors found", str(error_count))
    pr.toc()


if __name__ == "__main__":
    main()
