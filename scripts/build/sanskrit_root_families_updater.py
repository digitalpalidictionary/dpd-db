#!/usr/bin/env python3

"""Update Sanskrit root families in dpd.db from a curated TSV.

For each Pāḷi root family, looks up its Sanskrit root family from
`root_families_sanskrit.tsv` and injects it into the `sanskrit` column of
matching headwords as a bracketed annotation. Also regenerates the TSV from
db data so the file stays in sync.

Usage:
    uv run scripts/build/sanskrit_root_families_updater.py
"""

import csv
import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr

# the root == the word
exceptions = {
    "abhibhū",
    "abhijñāadhiprajñā",
    "anupādā",
    "hrī",
    "kṣudh",
    "medhā",
    "nidrā",
    "niṣṭhā",
    "parijñā",
    "pariṣad",
    "prabhā",
    "prajñā",
    "pratijñā",
    "pratimā",
    "pratipad",
    "puṣpa",
    "samavasthā",
    "saṃjñā",
    "saṃsthā",
    "upamā",
    "vidhā",
    "vidyut",
    "ājñā",
    "śraddhā",
}


class RootFamily:
    """Create a Root Family from db data."""

    def __init__(self, i: DpdHeadword, tsv_dict: dict[str, str]) -> None:
        self.root_key = i.root_key
        if i.rt is None:
            pr.red(f"!!! ERROR: `i.rt` is None for lemma_1: `{i.lemma_1}`")
            self.root_group = ""
            self.root_sign = ""
            self.root_meaning = ""
            self.sanskrit_root = ""
            self.sanskrit_root_class = ""
            self.sanskrit_root_meaning = ""
        else:
            self.root_group = i.rt.root_group
            self.root_sign = i.root_sign
            self.root_meaning = i.rt.root_meaning
            self.sanskrit_root = i.rt.sanskrit_root
            self.sanskrit_root_class = i.rt.sanskrit_root_class
            self.sanskrit_root_meaning = i.rt.sanskrit_root_meaning
        self.pali_root_family = i.family_root
        self.sanskrit_root_family = tsv_dict.get(i.root_family_key, "")
        self.sanskrit_dump = {i.sanskrit_clean}


def import_tsv_to_dict(pth: ProjectPaths) -> dict[str, str]:
    """Read tsv to dict."""
    tsv_dict = {}
    with pth.root_families_sanskrit_path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            try:
                key = f"{row['root_key']} {row['pali_root_family']}"
                tsv_dict[key] = row["sanskrit_root_family"]
            except KeyError:
                pr.red(f"!!! ERROR: {row}")
    return tsv_dict


def write_to_tsv(pth: ProjectPaths, root_dict: dict[str, "RootFamily"]) -> None:
    with pth.root_families_sanskrit_path.open(
        "w", newline="", encoding="utf-8"
    ) as csvfile:
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
            "sanskrit_dump",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()

        for key, i in root_dict.items():
            writer.writerow(
                {
                    "root_key": i.root_key,
                    "root_group": i.root_group,
                    "root_sign": i.root_sign,
                    "root_meaning": i.root_meaning,
                    "sanskrit_root": i.sanskrit_root,
                    "sanskrit_root_class": i.sanskrit_root_class,
                    "sanskrit_root_meaning": i.sanskrit_root_meaning,
                    "pali_root_family": i.pali_root_family,
                    "sanskrit_root_family": i.sanskrit_root_family,
                    "sanskrit_dump": ", ".join(
                        filter(None, pali_list_sorter(i.sanskrit_dump))
                    ),
                }
            )


def printer(counter: int, i: DpdHeadword, printer_on: bool) -> None:
    if printer_on:
        sanskrit_print = i.sanskrit.replace("[", r"\[")
        pr.white(f"{counter:<10}{i.lemma_1:<20}{i.family_root:<20}{sanskrit_print}")


def remove_sanskrit_root_family(sanskrit: str, sanskrit_root_family: str) -> str:
    """Strip an existing sanskrit root family token from the sanskrit string."""
    escaped = sanskrit_root_family.replace("+", "\\+")
    search_pattern = rf"(^|, |\b){escaped}($|, )"
    return re.sub(search_pattern, "", sanskrit)


def main() -> None:
    pr.tic()
    pr.yellow_title("update sanskrit root families")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    db = sorted(db, key=lambda x: pali_sort_key(x.root_family_key))

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
                    pr.green(i.root_family_key)

            else:
                if i.sanskrit_clean:
                    root_dict[i.root_family_key].sanskrit_dump.add(i.sanskrit_clean)

            # update the sanskrit root family:
            sanskrit_root_family = root_dict[i.root_family_key].sanskrit_root_family

            if sanskrit_root_family:
                if sanskrit_root_family != "-":
                    printer(counter, i, printer_on)

                    # first clean the square brackets
                    i.sanskrit = i.sanskrit_clean
                    printer(counter, i, printer_on)

                    # remove existing sanskrit root family
                    if sanskrit_root_family and sanskrit_root_family not in exceptions:
                        i.sanskrit = remove_sanskrit_root_family(
                            i.sanskrit, sanskrit_root_family
                        )
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
    pr.toc()


if __name__ == "__main__":
    main()
