#!/usr/bin/env python3

"""Create a dict of Sinhala POS short and long form"""

import json
import pandas as pd
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    df = pd.read_excel("exporter/sinhala/dpd sinhala test 1.1.xlsx")
    
    done = []
    eng_sing_pos_dict = {}
    for i in df.iterrows():
        si_id = i[1][0]
        pos_si = i[1][4]
        pos_si_full = i[1][5]
        if pos_si not in done:
            db = db_session.query(DpdHeadword.pos).filter(DpdHeadword.id == si_id).first()
            if db:
                eng_pos = db[0]
                eng_sing_pos_dict[eng_pos] = {
                    "pos_si": pos_si,
                    "pos_si_full": pos_si_full}
                done.append(pos_si)
    
    print(eng_sing_pos_dict)

    with open("temp/eng_sing_pos_dict.json", "w") as f:
        json.dump(eng_sing_pos_dict, f, ensure_ascii=False, indent=4 )
        




if __name__ == "__main__":
    main()
