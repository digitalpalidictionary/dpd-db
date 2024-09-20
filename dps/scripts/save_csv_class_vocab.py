#!/usr/bin/env python3

"""
    saving words for vocab pali class into separate csv and untute them to one xlsx
"""

import csv
import os
import pandas as pd
from db.models import DpdHeadword, SBS
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths
from rich.console import Console
from dps.tools.paths_dps import DPSPaths
from sqlalchemy.orm import joinedload

pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)

console = Console()


def main():
    print("saving words for vocab pali class")

    outputxlsx = os.path.join(dpspth.sbs_class_vocab_dir, 'vocab-for-classes.xlsx') 

    # Create the ExcelWriter object
    with pd.ExcelWriter(outputxlsx) as writer: # type: ignore
        # Save words for each class to a separate CSV file
        for sbs_class in range(2, 30):
            filename = os.path.join(dpspth.sbs_class_vocab_dir, f'vocab-class{sbs_class}.csv')
            save_words_to_csv(sbs_class, filename)
            save_csv_files_to_xlsx(sbs_class, filename, writer)

        # Close the session
        db_session.close()

def save_words_to_csv(sbs_class: int, filename: str):
    # Get all words that meet the conditions

    words = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).join(SBS).filter(
        SBS.sbs_class <= sbs_class,
        SBS.sbs_class_anki <= sbs_class
    ).all()

    # Open the CSV file and write the headers
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['pali', 'pos', 'meaning', 'root', 'construction', 'pattern',  'cl.']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Write each word to the CSV file
        for word in words:
            if word.rt:
                root_value = word.root_clean + " " + str(word.rt.root_group) + " " + word.root_sign + " (" + word.rt.root_meaning + ")"
            else:
                root_value = word.root_key

            writer.writerow({
                'pali': word.lemma_1,
                'pos': word.pos,
                'meaning': word.meaning_1,
                'root': root_value,
                'construction': word.construction,
                'pattern': word.pattern,
                'cl.': word.sbs.sbs_class
            })


def save_csv_files_to_xlsx(sbs_class: int, filename: str, writer):

    # Check if the file exists
    if not os.path.isfile(filename):
        print(f"File {filename} does not exist.")
        return

    # Read the CSV file into a DataFrame
    df = pd.read_csv(filename)

    # Sort the DataFrame by the "cl." column
    df = df.sort_values('cl.')

    # Get the base name of the CSV file without the extension
    sheet_name = os.path.basename(filename).split('.')[0]

    # Write the DataFrame to the Excel file
    df.to_excel(writer, sheet_name=sheet_name, index=False)


if __name__ == "__main__":
    main()

