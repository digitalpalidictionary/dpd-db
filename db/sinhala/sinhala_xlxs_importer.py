#!/usr/bin/env python3

"""Import Sinhala spreadsheet to database."""

import json
import pandas as pd
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Sinhala
from tools.paths import ProjectPaths
from tools.printer import p_green, p_no, p_title, p_yes
from tools.tic_toc import tic, toc


def main():
    tic()
    p_title("import sinhala xlsx to database")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db_session.execute(Sinhala.__table__.delete()) #type: ignore
    id_dict = get_id_dict()

    file_to_import = "db/sinhala/dpd sinhala 1.1.xlsx"
    si_df = pd.read_excel(file_to_import)

    for i in si_df.iterrows():
        si_id = i[1][0]
        meaning_si = i[1][2]
        si_checked = i[1][3]
        db = db_session.query(DpdHeadword).filter(DpdHeadword.id == si_id).first()
        if db:
            si_word = Sinhala()
            si_word.id = db.id
            si_word.meaning_si = meaning_si
            si_word.checked = si_checked
            db_session.add(si_word)
        else:
            if si_id in id_dict:
                si_word = Sinhala()
                new_id = id_dict[si_id]
                si_word.id = new_id
                si_word.meaning_si = meaning_si
                si_word.checked = si_checked
                db_session.add(si_word)
                print(f"[green]id updated from {si_id} to {new_id}")
            else:
                print(f"[red]{si_id} not in db")
    
    db_session.commit()

    toc()


def get_id_dict():
    p_green("loading id_dict.json")
    try:
        with open("temp/id_dict.json") as f:
            data = json.load(f)
            p_yes(len(data))
            return {int(key): value for key, value in data.items()}
    except FileNotFoundError:
        p_no("id_dict.json not found")
        return {}


if __name__ == "__main__":
    main()
