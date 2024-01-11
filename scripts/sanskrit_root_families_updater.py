#!/usr/bin/env python3

"""Update and replace Sanskrit root families from tsv data."""

import copy
import csv
import re

from db.models import PaliWord
from db.get_db_session import get_db_session

from tools.paths import ProjectPaths

# the root == the word
exceptions = ["saṃjñā", "śraddhā", "prajñā", "ājñā"]

class RootFamily():
    def __init__(self, row):
        self.root_key = row["root_key"]
        self.root_group = row["root_group"]
        self.root_sign = row["root_sign"]
        self.root_meaning = row["root_meaning"]
        self.sanskrit_root = row["sanskrit_root"]
        self.sanskrit_root_class = row["sanskrit_root_class"]
        self.sanskrit_root_meaning = row["sanskrit_root_meaning"]
        self.pali_root_family = row["pali_root_family"]
        self.sanskrit_root_family = row["sanskrit_root_family"]
        self.sanskrit_dump = set(row["sanskrit_dump"].split(", "))


def import_csv_to_root_family(csv_file_path):
    root_families = {}
    with open(csv_file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            key = f"{row['root_key']} {row['pali_root_family']}"
            root_families[key] = RootFamily(row)
    return root_families

def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()

    tsv_path = pth.root_families_sanskrit_path
    root_dict = import_csv_to_root_family(tsv_path)

    counter = 1
    for i in db:
        if (
            i.root_key
            and i.family_root
        ):
            # root_family_key = f"{i.root_key} {i.family_root}"
            r = root_dict.get(i.root_family_key)
            
            if r:
                if r.sanskrit_root_family:
                    print(f"{counter:<10}{i.pali_1:<20}{i.family_root:<20}{i.sanskrit}")

                    # remove any sqaure brackets at the end
                    if "[" in i.sanskrit:
                        # old_sanskrit = copy.deepcopy(i.sanskrit)
                        i.sanskrit = re.sub(r"\[.+\]", "", i.sanskrit)
                        print(f"{counter:<10}{i.pali_1:<20}{i.family_root:<20}{i.sanskrit}")
                    
                    # remove old values
                    if r.sanskrit_root_family not in exceptions:
                        escaped_sanskrit_root_family = r.sanskrit_root_family.replace('+', '\\+')
                        remove = fr"(^|, |\[|\b){escaped_sanskrit_root_family}($|, |\])"
                        i.sanskrit = re.sub(remove, "", i.sanskrit)
                        print(f"{counter:<10}{i.pali_1:<20}{i.family_root:<20}{i.sanskrit}")

                    # add new value
                    i.sanskrit = i.sanskrit.strip() + f" [{r.sanskrit_root_family}]"
                    i.sanskrit = i.sanskrit.strip()
                    print(f"{counter:<10}{i.pali_1:<20}{i.family_root:<20}{i.sanskrit}\n")
                    counter += 1
    
    db_session.commit()


if __name__ == "__main__":
    main()

