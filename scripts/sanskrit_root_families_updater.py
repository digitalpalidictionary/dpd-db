#!/usr/bin/env python3

"""
1. Update and replace Sanskrit root families from tsv data.
2. Update tsv from db data and write to tsv."""

import csv
import re
from rich import print
from db.models import DpdHeadwords
from db.get_db_session import get_db_session

from tools.paths import ProjectPaths
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.tic_toc import tic, toc

# the root == the word
exceptions = ["saṃjñā", "śraddhā", "prajñā", "ājñā", "pratijñā"]


class RootFamily():
    """Create a Root Family from db data."""
    def __init__(self, i, tsv_dict):
        self.root_key = i.root_key
        self.root_group = i.rt.root_group
        self.root_sign = i.root_sign
        self.root_meaning = i.rt.root_meaning
        self.sanskrit_root = i.rt.sanskrit_root
        self.sanskrit_root_class = i.rt.sanskrit_root_class
        self.sanskrit_root_meaning = i.rt.sanskrit_root_meaning
        self.pali_root_family = i.family_root
        self.sanskrit_root_family = tsv_dict.get(i.root_family_key, "")
        self.sanskrit_dump = set([i.sanskrit_clean])


def import_tsv_to_dict(pth):
    """Read tvs to dict."""
    tsv_dict = {}
    with open(pth.root_families_sanskrit_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            key = f"{row['root_key']} {row['pali_root_family']}"
            tsv_dict[key] = row["sanskrit_root_family"]
    return tsv_dict


def write_to_tsv(pth, root_dict) -> None:
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
                    "pali_root_family": i.pali_root_family,
                    "sanskrit_root_family": i.sanskrit_root_family,
                    "sanskrit_dump": ", ".join(filter(None, pali_list_sorter(i.sanskrit_dump)))
                })


def printer(counter, i, printer_on):
    if printer_on:
        sanksrit_print = i.sanskrit.replace("[", r"\[")
        print(f"{counter:<10}{i.lemma_1:<20}{i.family_root:<20}{sanksrit_print}")

def main():
    tic()
    print("[bright_yellow]update sanskrit root families")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadwords).all()
    db = sorted(
        db, key=lambda x: (pali_sort_key(x.root_family_key)))

    tsv_dict = import_tsv_to_dict(pth)
    root_dict = {}
    printer_on = False

    counter = 1
    for i in db:
        if i.root_key and i.family_root:

            # add the family or update sanskrit_dump
            if i.root_family_key not in root_dict:
                root_dict[i.root_family_key] = RootFamily(i, tsv_dict)
                
                # print out new root families
                if i.root_family_key not in tsv_dict:
                    print(i.root_family_key)

            else:
                if i.sanskrit_clean:
                    root_dict[i.root_family_key].sanskrit_dump.add(i.sanskrit_clean)

            # update the sanskrit root family:
            sanskrit_root_family = root_dict[i.root_family_key].sanskrit_root_family

            if sanskrit_root_family:
                printer(counter, i, printer_on)

                # first clean the square brackets
                i.sanskrit = i.sanskrit_clean
                printer(counter, i, printer_on)

                # remove existing sanskrit root family
                if sanskrit_root_family and sanskrit_root_family not in exceptions:
                    escaped_sanskrit_root_family = sanskrit_root_family.replace('+', '\\+')
                    search_pattern = fr"(^|, ||\b){escaped_sanskrit_root_family}($|, )"
                    i.sanskrit = re.sub(search_pattern, "", i.sanskrit)
                    printer(counter, i, printer_on)

                # add new value                    
                if i.sanskrit:
                    i.sanskrit = f"{i.sanskrit.strip()} [{sanskrit_root_family}]"
                else:
                    i.sanskrit = f"[{sanskrit_root_family}]"
                printer(counter, i, printer_on)

                counter += 1
            
    db_session.commit()
    write_to_tsv(pth, root_dict)
    toc()


if __name__ == "__main__":
    main()

