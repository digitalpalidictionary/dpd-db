#!/usr/bin/env python3

"""Find 1000 most common words in DPD."""

import csv

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main() -> None:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = (
        db_session.query(DpdHeadword).order_by(DpdHeadword.ebt_count.desc()).limit(2000)
    )

    most_common: list[DpdHeadword] = []
    for counter, i in enumerate(db):
        if i.meaning_1.startswith("(gram)"):
            pass
        elif i.meaning_1 == "":
            pass
        elif i.source_1 == "-":
            pass
        elif i.source_1 == "":
            pass
        elif len(most_common) == 1000:
            break
        else:
            most_common.append(i)

    for counter, i in enumerate(most_common):
        print(counter + 1, i.lemma_1, i.ebt_count)

    column_names = [
        column.name
        for column in DpdHeadword.__mapper__.columns
        if not column.name.startswith(("inflection", "freq"))
    ]

    with open("temp/1000_most_common_words.tsv", "w", newline="") as f:
        csvwriter = csv.writer(f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        csvwriter.writerow(column_names)
        for i in most_common:
            csvwriter.writerow([getattr(i, name) for name in column_names])

    db_session.close()


if __name__ == "__main__":
    main()
