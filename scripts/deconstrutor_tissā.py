#!/usr/bin/env python3

"""Change tissa / tissā to iti assa / iti assā."""

import re
from rich import print

from db.db_helpers import get_db_session
from db.models import Sandhi
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc


def main():
    tic()
    print("[bright_yellow]fixing tissa and tissā")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(Sandhi).all()
    counter = 1
    for s in db:
        
        # tissā > iti + assā
        if re.search(r"tissā$", s.sandhi):
            for index, split in enumerate(s.split_list):
                if re.search(" tissā$", split):
                    new_split_list = s.split_list
                    new_split = re.sub(" tissā$", " iti + assā", split)
                    if new_split not in s.split_list:
                        new_split_list.insert(index, new_split)
                        s.split = ",".join(new_split_list)
                        printer (counter, s, index)
                        counter += 1
        
        # tissa> iti + assa
        if re.search(r"tissa$", s.sandhi):
            for index, split in enumerate(s.split_list):
                if re.search(" tissa$", split):
                    new_split_list = s.split_list
                    new_split = re.sub(" tissa$", " iti + assa", split)
                    if new_split not in s.split_list:
                        new_split_list.insert(index, new_split)
                        s.split = ",".join(new_split_list)
                        printer (counter, s, index)
                        counter += 1
    
    db_session.commit()
    toc()


def printer (counter, s, index):
    print(f"{counter:<10}[cyan]{s.sandhi:<50}[green]{s.split_list}")
     
if __name__ == "__main__":
    main()
