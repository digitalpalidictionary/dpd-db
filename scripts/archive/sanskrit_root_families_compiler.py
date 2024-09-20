#!/usr/bin/env python3

"""Export a tsv of all Pali Root Families for adding Sanskrit lemma."""

import csv


from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.pali_sort_key import pali_sort_key


class RootFamily():
    def __init__(self, i: DpdHeadword) -> None:
        self.root_family_key = i.root_family_key
        self.root_key: str = i.root_key
        self.root_group: str = str(i.rt.root_group)
        self.root_sign: str = i.rt.root_sign
        self.root_meaning: str = i.rt.root_meaning
        self.sanskrit_root: str = i.rt.sanskrit_root
        self.sanskrit_root_class: str = str(i.rt.sanskrit_root_class)
        self.sanskrit_root_meaning: str = i.rt.sanskrit_root_meaning
        self.root_family: str = i.family_root
        if i.sanskrit:
            self.sanskrit: set = {i.sanskrit}
        else:
            self.sanskrit: set = set()
    
    def __repr__(self) -> str:
        return f"""
{self.root_family_key}
{self.root_key}
{self.root_group} {self.root_sign} {self.root_meaning}
{self.sanskrit_root} {self.sanskrit_root_class} {self.sanskrit_root_meaning}
{self.root_family}
{self.sanskrit}
"""
               

def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    db = sorted(
        db, key=lambda x: (pali_sort_key(x.root_key), pali_sort_key(x.family_root)))

    root_dict = {}
    for i in db:
        if i.root_key:
            root_family_key = i.root_family_key
            if root_family_key not in root_dict:
                root_dict[root_family_key] = RootFamily(i)
            else:
                if i.sanskrit:
                    root_dict[root_family_key].sanskrit.add(i.sanskrit)
    
    return
    # writing is disable in case of stupidity.
    with open(
        pth.root_families_sanskrit_path, "w", newline="") as csvfile:
        fieldnames = [
            "root_key",
            "root_group",
            "root_sign",
            "root_meaning",
            "sanskrit_root",
            "sanskrit_root_class",
            "sanskrit_root_meaning",
            "pali_root_family",
            "sanskrit_root_family",
            "sanskrit_dump"
            ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()

        for key, i in root_dict.items():
                writer.writerow({
                    "root_key": i.root_key,
                    "root_group": i.root_group,
                    "root_sign": i.root_sign,
                    "root_meaning": i.root_meaning,
                    "sanskrit_root": i.sanskrit_root,
                    "sanskrit_root_class": i.sanskrit_root_class,
                    "sanskrit_root_meaning": i.sanskrit_root_meaning,
                    "pali_root_family": i.root_family,
                    "sanskrit_root_family": "",
                    "sanskrit_dump": ", ".join(i.sanskrit)
                })


if __name__ == "__main__":
    main()
