#!/usr/bin/env python3

"""Find duplicate examples in sbs_example_1,2,3,4 and save all ids of words with similar or identical examples in csv"""
import csv

from difflib import SequenceMatcher

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths

from sqlalchemy.orm import joinedload

from rich.console import Console
from tools.tic_toc import tic, toc

console = Console()

threshold=0.84

def main():

    tic()
    console.print("[bold yellow]Saving id of similar and identical sbs_examples")
    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).all()

    ids_to_save = set()

    for i in db:
        if i.sbs and (i.sbs.sbs_index or i.sbs.sbs_category or i.sbs.sbs_class_anki):
            examples = [i.sbs.sbs_example_1, i.sbs.sbs_example_2, i.sbs.sbs_example_3, i.sbs.sbs_example_4]
            for idx1, example1 in enumerate(examples):
                for idx2, example2 in enumerate(examples):
                    if idx1 < idx2:
                        if example1 and example2:
                            if example1 == example2 or paragraphs_are_similar(example1, example2):
                                ids_to_save.add(i.id)

    with open(dpspth.id_temp_list_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for _id in ids_to_save:
            writer.writerow([_id])

    # Counting rows in the CSV file
    with open(dpspth.id_temp_list_path, 'r', newline='') as csvfile:
        row_count = sum(1 for row in csvfile)

    console.print(f"[bold green]IDs written to {dpspth.id_temp_list_path}")
    console.print(f"[bold cyan]Number of rows of unique IDs extracted: {row_count}")

    toc()


def paragraphs_are_similar(paragraph1, paragraph2, threshold=threshold):
    matcher = SequenceMatcher(None, paragraph1, paragraph2)
    similarity_ratio = matcher.ratio()
    return similarity_ratio >= threshold


if __name__ == "__main__":
    main()
