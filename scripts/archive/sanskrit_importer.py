#!/usr/bin/env python3

"""Import Ram's Sanskrit additions."""


import pandas as pd
import pickle

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()

    # setup sanskrit dict
    df = pd.read_excel("db/sanskrit/DPD Sanskrit Updates v1.xlsx", index_col=0)
    df = df.fillna("")
    df = df.rename(columns={"sanskrit": "sanskrit_old", "sanskrit2": "sanskrit_new"})
    sk_dict = df[["lemma_1", "sanskrit_old", "sanskrit_new"]].to_dict(orient="index")
    
    # setup db session
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    counter = 0
    for i in db:
        if i.id in sk_dict:
            # update the old sanskrit value in the dict
            sk_dict[i.id]["sanskrit_old"] = i.sanskrit

            # update the db with the new value
            i.sanskrit = sk_dict[i.id]["sanskrit_new"]

            # print(f"{counter:<5}{i.id:<10}{sk_dict[i.id]['sanskrit_old']:<30}{i.sanskrit:}")
            counter += 1

    with open("db/sanskrit/sanskrit_update_1", "wb") as f:
        pickle.dump(sk_dict, f)
    
    db_session.commit()

if __name__ == "__main__":
    main()
