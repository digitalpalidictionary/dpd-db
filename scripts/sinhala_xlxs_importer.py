#!/usr/bin/env python3

"""Import Sinhala spreadsheet to database."""

import json
import pandas as pd
from rich import print

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, Sinhala
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db_session.execute(Sinhala.__table__.delete()) #type: ignore
    si_df = pd.read_excel("temp/dpd sinhala test 1.1.xlsx")
    id_dict = get_id_dict()

    missing_error = 0

    for i in si_df.iterrows():
        si_id = i[1][0]
        si_meaning = i[1][2]
        db = db_session.query(DpdHeadwords).filter(DpdHeadwords.id == si_id).first()
        if db:
            si_word = Sinhala()
            si_word.id = db.id
            si_word.si_meaning = si_meaning
            db_session.add(si_word)
        else:
            if si_id in id_dict:
                si_word = Sinhala()
                new_id = id_dict[si_id]
                si_word.id = new_id
                si_word.si_meaning = si_meaning
                db_session.add(si_word)
                print(f"[green]id updated from {si_id} to {new_id}")
            else:
                print(f"[red]{si_id} not in db")
                missing_error += 1
    
    db_session.commit()
    print(missing_error)


def get_id_dict():
    with open("temp/id_dict.json") as f:
        data = json.load(f)
        return {int(key): value for key, value in data.items()}


if __name__ == "__main__":
    main()
