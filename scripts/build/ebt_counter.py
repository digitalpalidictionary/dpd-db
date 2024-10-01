#!/usr/bin/env python3

"""
Calculate the number of occurrences of a word's inflections 
in early texts and add to db.
EBT books are VIN1, VIN2, DN, MN, SN, AN and KN1
"""

import json
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import p_green, p_title, p_yes
from tools.tic_toc import tic, toc
from tools.pali_text_files import ebts

def main():

    tic()
    p_title("calculating frequency in ebts")
    p_green("setting up")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    with open(pth.cst_file_freq) as f:
        cst_file_freq_dict = json.load(f)
    
    db = db_session.query(DpdHeadword).all()

    ebt_files = [ebt_file.replace(".txt", ".xml") for ebt_file in ebts]
    p_yes("ok")

    p_green("calculating")
    for i in db:
        total = 0
        inflections = i.inflections_list_all
        for ebt_file in ebt_files:
            file_freq = cst_file_freq_dict[ebt_file]
            for inflection in inflections:
                total += file_freq.get(inflection, 0)
        i.ebt_count = total
    p_yes("ok")

    p_green("saving to db")
    db_session.commit()
    p_yes("ok")

    toc()


if __name__ == "__main__":
    main()

