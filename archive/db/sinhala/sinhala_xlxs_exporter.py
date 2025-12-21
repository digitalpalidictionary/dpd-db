#!/usr/bin/env python3

"""Export Sinhala database to spreadsheet for new additions."""

import pandas as pd

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.tic()
    pr.title("export sinhala db to xlsx")

    file_output = "db/sinhala/dpd sinhala 1.2.xlsx"

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    db_length = len(db)

    column_names = ["id", "lemma_si", "pos_si", "en_meaning", "meaning_si", "checked"]

    si_data: list[tuple] = []

    pr.green_title("making data tuples")
    for count, i in enumerate(db):
        if i.si:
            si_data.append(
                (
                    i.id,
                    i.lemma_si,
                    i.pos_si,
                    i.meaning_combo,
                    i.si.meaning_si,
                    i.si.checked,
                )
            )
        else:
            si_data.append((i.id, i.lemma_si, i.pos_si, i.meaning_combo, "", "✘"))

        if count % 5000 == 0:
            pr.counter(count, db_length, i.lemma_1)

    pr.green("making pandas df")
    df = pd.DataFrame(si_data, columns=column_names)
    pr.yes(len(df))

    pr.green("exporting to xlsx")
    df.to_excel(file_output, index=False)
    pr.yes("ok")

    pr.toc()


if __name__ == "__main__":
    main()
