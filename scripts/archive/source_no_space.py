#!/usr/bin/env python3

"""Remove spaces from sutta sodes"""
import re
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.pali_sort_key import pali_list_sorter


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    sutta_codes = set()
    find_me = "VIN "
    replace_me = "VIN"
    for i in db:
        if find_me != "":
            if re.match(r"^VIN \d", i.source_1):
                if i.source_1.startswith(find_me):
                    i.source_1 =  i.source_1.replace(find_me, replace_me)
                    print(i.source_1)

            if re.match(r"^VIN \d", i.source_2):
                if i.source_2.startswith(find_me):
                    i.source_2 =  i.source_2.replace(find_me, replace_me)
                    print(i.source_2)

        # # add to sutta_codes set 
        # if " " in i.source_1:
        #     sutta_codes.add(i.source_1)
        # if " " in i.source_2:
        #     sutta_codes.add(i.source_2)
    
    with open("temp/source.txt", "w") as f:
        sutta_codes_sorted = pali_list_sorter(sutta_codes)
        for s in sutta_codes_sorted:
            f.write(f"{s}\n")

    if replace_me != "":
        db_session.commit()


if __name__ == "__main__":
    main()
