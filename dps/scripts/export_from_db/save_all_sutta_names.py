#!/usr/bin/env python3

"""Filter all sutta names and save them"""

from db.models import DpdHeadword
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from db.db_helpers import get_db_session
import csv
from rich.console import Console

from tools.printer import printer as pr

from exporter.goldendict.export_epd import extract_sutta_numbers

console = Console()


def save_filtered_words():
    pr.tic()
    console.print("[bold bright_yellow]filtering words from db by some condition")

    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db = (
        db_session.query(DpdHeadword)
        .filter(
            DpdHeadword.family_set.startswith("suttas of the"),
            DpdHeadword.meaning_2 != "",
        )
        .all()
    )

    # Filter words
    filtered_words = [word for word in dpd_db]

    # Write to CSV using tab as delimiter
    with open(dpspth.temp_csv_path, "w", newline="") as csvfile:
        fieldnames = ["sutta_number", "sutta_name"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter="\t")

        writer.writeheader()  # Write the header

        for word in filtered_words:
            sutta_numbers = extract_sutta_numbers(word.meaning_2)
            sutta_number = next((num for num in sutta_numbers if num is not None), None)
            writer.writerow(
                {
                    "sutta_number": sutta_number,
                    "sutta_name": word.lemma_2,
                }
            )

    db_session.close()

    print(f"[green]saved into {dpspth.temp_csv_path}")

    pr.toc()


# Call the function
save_filtered_words()
