import csv
import os
import pandas as pd
from db.models import PaliWord, SBS
from db.get_db_session import get_db_session
from tools.paths import ProjectPaths
from rich.console import Console
from dps.tools.paths_dps import DPSPaths


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

    words = db_session.query(PaliWord).join(SBS).filter(
        SBS.sbs_class <= sbs_class,
        SBS.sbs_class_anki <= sbs_class
    ).all()

    # Open the CSV file and write the headers
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['pali_1', 'pos', 'meaning_1', 'root', 'pattern',  'sbs_class']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Write each word to the CSV file
        for word in words:
            writer.writerow({
                'pali_1': word.pali_1,
                'pos': word.pos,
                'meaning_1': word.meaning_1,
                'root': word.root_key,
                'pattern': word.pattern,
                'sbs_class': word.sbs.sbs_class
            })


def save_csv_files_to_xlsx(sbs_class: int, filename: str, writer):
    # Check if the file exists
    if not os.path.isfile(filename):
        print(f"File {filename} does not exist.")
        return

    # Read the CSV file into a DataFrame
    df = pd.read_csv(filename)

    # Get the base name of the CSV file without the extension
    sheet_name = os.path.basename(filename).split('.')[0]

    # Write the DataFrame to the Excel file
    df.to_excel(writer, sheet_name=sheet_name, index=False)


if __name__ == "__main__":
    main()

