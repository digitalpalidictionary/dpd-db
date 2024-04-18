#!/usr/bin/env python3

"""Export family data to JSON."""

import json
from rich import print

from db.get_db_session import get_db_session
from db.models import FamilyCompound, FamilyRoot
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    cf_db = db_session.query(FamilyCompound).all()
    rf_db = db_session.query(FamilyRoot).all()

    cf_dict = {}
    for i in cf_db:
        cf_dict[i.compound_family] = {
            "count": i.count,
            "data": i.data_unpack}

    with open("temp/compound_families.json", "w") as f:
        json.dump(cf_dict, f, ensure_ascii=False, indent=0)
    
    rf_dict = {}
    for i in rf_db:
        rf_dict[i.root_family_key] = {
            "root_key": i.root_key,
            "root_family": i.root_family,
            "root_meaning": i.root_meaning,
            "count": i.count,
            "data": i.data_unpack}

    with open("temp/root_families.json", "w") as f:
        json.dump(rf_dict, f, ensure_ascii=False, indent=0)



if __name__ == "__main__":
    main()
