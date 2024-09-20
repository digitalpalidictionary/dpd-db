#!/usr/bin/env python3

"""
How many words in CST and SC texts?
Whats the size difference?
"""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.cst_sc_text_sets import make_cst_text_set, make_sc_text_set
from tools.paths import ProjectPaths

all_texts = [
    "vin1", "vin2", "vin3", "vin4", "vin5",
    "dn1", "dn2", "dn3",
    "mn1", "mn2", "mn3",
    "sn1", "sn2", "sn3", "sn4", "sn5",
    "an1", "an2", "an3", "an4", "an5",
    "an6", "an7", "an8", "an9", "an10", "an11",
    "kn1", "kn2", "kn3", "kn4", "kn5",
    "kn6", "kn7", "kn8", "kn9", "kn10",
    "kn11", "kn12", "kn13", "kn14", "kn15",
    "kn16", "kn17", "kn18", "kn19", "kn20",
    "abh1", "abh2", "abh3", "abh4", "abh5", "abh6", "abh7",
    "vina",
    "dna",
    "mna",
    "sna",
    "ana",
    "kn1a",
    "kn2a",
    "kn3a",
    "kn4a",
    "kn5a",
    "kn6a",
    "kn7a",
    "kn8a",
    "kn9a",
    "kn10a",
    "kn11a",
    "kn12a",
    "kn13a",
    "kn14a",
    "kn15a",
    "kn16a",
    "kn17a",
    "kn19a",
    "abha",
    "vint",
    "dnt",
    "mnt",
    "snt",
    "ant",
    "knt",
    "abht",
    "vism",
    "visma",
    "ap",
    "apt",
    "anna",
    ]


def main():
    pth = ProjectPaths()
    cst_text_set = make_cst_text_set(pth, all_texts)
    sc_text_set = make_sc_text_set(pth, all_texts)
    print(f"{'CST:':<10}{len(cst_text_set):,}")
    print(f"{'SC:':<10}{len(sc_text_set):,}")
    print(f"{'DIFF:':<10}{len(cst_text_set) - len(sc_text_set):,}")


if __name__ == "__main__":
    main()
