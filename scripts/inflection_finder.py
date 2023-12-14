#!/usr/bin/env python3

"""Find a specific inflection in the derivated_data table."""

import re
from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths

find_me = "āma$" 

def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()
    for counter, i in enumerate(db):
        if i.pos == "aor":
            if i.dd:
                inflections_list = i.dd.inflections.split(",")
                for inflection in inflections_list:
                    if re.findall(find_me, inflection):
                        print(f"{i.pali_1:<20}: {inflection}")


if __name__ == "__main__":
    main()
