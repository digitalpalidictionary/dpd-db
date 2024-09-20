#!/usr/bin/env python3

"""Convert pickle to json file"""

import copy
import json
import pickle
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    with open(pth.syn_var_exceptions_old_path, "rb") as f:
        exceptions_list: list = pickle.load(f)
    print(len(exceptions_list)) 
    
    new_exceptions_set: set = set()
    for i in exceptions_list:
        if "[" in i:
            new_exceptions_set.add(i)

    print(len(new_exceptions_set))
    with open(pth.syn_var_exceptions_path, "w") as f:
        json.dump(list(new_exceptions_set), f, ensure_ascii=False, indent=2)



if __name__ == "__main__":
    main()
