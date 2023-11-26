#!/usr/bin/env python3

"""Remove spaces from sutta sodes"""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths
from tools.pali_sort_key import pali_list_sorter


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()
    sutta_codes = set()
    find_me = "KHPa "
    replace_me = "KHPa"
    for i in db:
        if find_me != "":
            if i.source_1.startswith(find_me):
                i.source_1 =  i.source_1.replace(find_me, replace_me)
            if i.source_2.startswith(find_me):
                i.source_2 =  i.source_2.replace(find_me, replace_me)

        # add to sutta_codes set 
        if " " in i.source_1:
            sutta_codes.add(i.source_1)
        if " " in i.source_2:
            sutta_codes.add(i.source_2)
    
    with open("temp/sutta_code.txt", "w") as f:
        sutta_codes_sorted = pali_list_sorter(sutta_codes)
        for s in sutta_codes_sorted:
            f.write(f"{s}\n")

    if find_me != "":
        db_session.commit()


if __name__ == "__main__":
    main()
