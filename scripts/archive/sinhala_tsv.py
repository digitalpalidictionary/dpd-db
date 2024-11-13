#!/usr/bin/env python3

"""Export .tsv of data for Sinhala translation."""

import pandas as pd

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tsv_read_write import write_tsv_list
from tools.meaning_construction import make_meaning_combo

def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    data = []
    for counter, i in enumerate(db):
        meaning = make_meaning_combo(i)
        if i.meaning_1:
            test = "✔"
        else:
            test = "✘"
        
        row = [i.id, i.lemma_1, i.pos, meaning, test, ""]
        data.append(row)

    headers = ["id", "lemma_1", "pos", "english", "check", "sinhala"]
    
    
    # write tsv
    write_tsv_list("temp/dpd_sinhala.tsv", headers, data)

    # write xlsx
    df = pd.DataFrame(data, columns=headers)
    df.to_excel("temp/dpd_sinhala_.xlsx", index=False)

if __name__ == "__main__":
    main()
