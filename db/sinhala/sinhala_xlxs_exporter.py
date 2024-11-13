#!/usr/bin/env python3

"""Export Sinhala database to spreadsheet for new additions."""

import pandas as pd

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green, p_green_title, p_title, p_yes
from tools.tic_toc import tic, toc


def main():
    tic()
    p_title("export sinhala db to xlsx")

    file_output = "db/sinhala/dpd sinhala 1.2.xlsx"

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    db_length = len(db)

    column_names = [
        "id",
        "lemma_si",
        "pos_si",
        "en_meaning",
        "meaning_si",
        "checked" 
    ]

    si_data: list[tuple] = []

    p_green_title("making data tuples")
    for count, i in enumerate(db):
        if i.si:
            si_data.append((
                i.id,
                i.lemma_si,
                i.pos_si,
                i.meaning_combo,
                i.si.meaning_si,
                i.si.checked
            ))
        else:
            si_data.append((
                i.id,
                i.lemma_si,
                i.pos_si,
                i.meaning_combo,
                "",
                "✘"
            ))

        if count % 5000 == 0:
            p_counter(count, db_length, i.lemma_1)
        
    p_green("making pandas df")
    df = pd.DataFrame(si_data, columns=column_names)
    p_yes(len(df))

    p_green("exporting to xlsx")
    df.to_excel(file_output, index=False)
    p_yes("ok")

    toc()

if __name__ == "__main__":
    main()
