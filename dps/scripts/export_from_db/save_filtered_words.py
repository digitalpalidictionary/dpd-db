#!/usr/bin/env python3

"""Filter words based on some codition and save into csv (with backing up existing temp csv)"""

from db.models import DpdHeadword, SBS
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from db.db_helpers import get_db_session
import csv
import os
import shutil
from rich.console import Console

from tools.printer import printer as pr
from datetime import datetime


console = Console()


def save_filtered_words():
    pr.tic()
    console.print("[bold bright_yellow]filtering words from db by some condition")

    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    attribute = "3"

    dpd_db = (
        db_session.query(DpdHeadword)
        .outerjoin(SBS, DpdHeadword.id == SBS.id)
        .filter(SBS.sbs_class_anki == attribute)
        .all()
    )

    # Filter words
    filtered_words = [word for word in dpd_db]

    # Check if the CSV exists, and create a backup with a timestamp if it does
    if os.path.exists(dpspth.temp_csv_path):
        timestamp = datetime.now().strftime("%y%m%d%H%M")
        base_name = os.path.basename(dpspth.temp_csv_path).replace(".csv", "")

        # Ensure the backup directory exists, if not, create it
        if not os.path.exists(dpspth.temp_csv_backup_dir):
            os.makedirs(dpspth.temp_csv_backup_dir)

        print(f"[green]backup existing csv into {dpspth.temp_csv_backup_dir}")

        backup_name = os.path.join(
            dpspth.temp_csv_backup_dir, f"{base_name}_backup_{timestamp}.csv"
        )
        shutil.copy(dpspth.temp_csv_path, backup_name)

    # Write to CSV using tab as delimiter
    with open(dpspth.temp_csv_path, "w", newline="") as csvfile:
        fieldnames = [
            "id",
            "lemma_1",
            "meaning_1",
            "sbs_class_anki",
            "class_source",
            "class_sutta",
            "class_example",
            "sbs_source_1",
            "sbs_sutta_1",
            "sbs_example_1",
            "sbs_source_2",
            "sbs_sutta_2",
            "sbs_example_2",
            "sbs_source_3",
            "sbs_sutta_3",
            "sbs_example_3",
            "sbs_source_4",
            "sbs_sutta_4",
            "sbs_example_4",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter="\t")

        writer.writeheader()  # Write the header

        for word in filtered_words:
            writer.writerow(
                {
                    "id": word.id,
                    "lemma_1": word.lemma_1,
                    "meaning_1": word.meaning_1,
                    "sbs_class_anki": word.sbs.sbs_class_anki,
                    "class_source": word.sbs.class_source,
                    "class_sutta": word.sbs.class_sutta,
                    "class_example": word.sbs.class_example,
                    "sbs_source_1": word.sbs.sbs_source_1,
                    "sbs_sutta_1": word.sbs.sbs_sutta_1,
                    "sbs_example_1": word.sbs.sbs_example_1,
                    "sbs_source_2": word.sbs.sbs_source_2,
                    "sbs_sutta_2": word.sbs.sbs_sutta_2,
                    "sbs_example_2": word.sbs.sbs_example_2,
                    "sbs_source_3": word.sbs.sbs_source_3,
                    "sbs_sutta_3": word.sbs.sbs_sutta_3,
                    "sbs_example_3": word.sbs.sbs_example_3,
                    "sbs_source_4": word.sbs.sbs_source_4,
                    "sbs_sutta_4": word.sbs.sbs_sutta_4,
                    "sbs_example_4": word.sbs.sbs_example_4,
                }
            )

    db_session.close()

    print(f"[green]saved into {dpspth.temp_csv_path}")

    pr.toc()


# Call the function
save_filtered_words()
