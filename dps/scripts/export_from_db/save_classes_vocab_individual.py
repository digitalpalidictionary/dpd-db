#!/usr/bin/env python3

"""
    saving words for vocab pali class into separate csv and untute them to one xlsx and converting them into separate XLSX/HTML outputs.
"""

import pandas as pd
import os
from string import Template
import csv
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
    print("saving vocab for classes one by one...")

    outputxlsx = os.path.join(dpspth.pali_class_vocab_html_dir, 'vocab-for-classes.xlsx') 

    # save vocab for HTML
    with pd.ExcelWriter(outputxlsx) as writer: # type: ignore
        total_words_saved = 0
        # Save words for each class to a separate CSV file
        for sbs_class in range(2, 30):
            filename = os.path.join(dpspth.sbs_class_vocab_dir, f'vocab-class{sbs_class}.csv')
            words_saved = save_words_to_csv(sbs_class, filename)

            if words_saved:
                total_words_saved += words_saved
                save_csv_files_to_xlsx(filename, writer)

        print(f"Total words saved to all CSVs: {total_words_saved}")

    print("saving words with examples for vocab pali class")
    # save vocab with examples
    for sbs_class in range(2, 30):
        filename = os.path.join(dpspth.pali_class_vocab_dir, f'vocab_class_{sbs_class}.csv')
        save_words_with_examples_to_csv(sbs_class, filename)

    # Close the session
    db_session.close()

    convert_csv_to_html()


def save_words_to_csv(sbs_class: int, filename: str) -> int:
    """
    Save words for a specific class to a CSV file.
    :param sbs_class: Class number.
    :param filename: Output CSV file path.
    :return: Number of words saved.
    """
    

    words = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).join(SBS).filter(
        SBS.sbs_class <= sbs_class,
        SBS.sbs_class_anki <= sbs_class
    ).all()

    words_saved = 0

    # Open the CSV file and write the headers
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['pali', 'pos', 'meaning', 'root', 'construction', 'pattern',  'cl.']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Write each word to the CSV file
        for word in words:
            if word.rt:
                root_value = f"{word.root_clean} {word.rt.root_group} {word.root_sign} ({word.rt.root_meaning})"
            else:
                root_value = word.root_key

            writer.writerow({
                'pali': word.lemma_1,
                'pos': word.pos,
                'meaning': word.meaning_1,
                'root': root_value,
                'construction': word.construction_line1,
                'pattern': word.pattern,
                'cl.': word.sbs.sbs_class
            })
            words_saved += 1

    return words_saved


def save_words_with_examples_to_csv(sbs_class: int, filename: str):
    # Get all words that meet the conditions
    

    words = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).join(SBS).filter(
        SBS.sbs_class_anki == sbs_class
    ).all()

    # Open the CSV file and write the headers
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = [
            'pali', 'pos', 'meaning', 'source_1', 'sutta_1', 'example_1', 
            'source_2', 'sutta_2', 'example_2',
            'source_3', 'sutta_3', 'example_3',
            'source_4', 'sutta_4', 'example_4',
            ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Write each word to the CSV file
        for word in words:

            writer.writerow({
                'pali': word.lemma_1,
                'pos': word.pos,
                'meaning': word.meaning_1,
                'source_1': word.sbs.sbs_source_1,
                'sutta_1': word.sbs.sbs_sutta_1,
                'example_1': word.sbs.sbs_example_1,
                'source_2': word.sbs.sbs_source_2,
                'sutta_2': word.sbs.sbs_sutta_2,
                'example_2': word.sbs.sbs_example_2,
                'source_3': word.sbs.sbs_source_3,
                'sutta_3': word.sbs.sbs_sutta_3,
                'example_3': word.sbs.sbs_example_3,
                'source_4': word.sbs.sbs_source_4,
                'sutta_4': word.sbs.sbs_sutta_4,
                'example_4': word.sbs.sbs_example_4,
            })


def save_csv_files_to_xlsx(filename: str, writer):
    """
    Append a CSV file to an Excel file as a new sheet.
    :param filename: Path to the CSV file.
    :param writer: Pandas ExcelWriter object.
    """
    if not os.path.isfile(filename):
        print(f"File {filename} does not exist.")
        return

    df = pd.read_csv(filename).sort_values('cl.')

    # Get the base name of the CSV file without the extension
    sheet_name = os.path.basename(filename).split('.')[0]

    # Write the DataFrame to the Excel file
    df.to_excel(writer, sheet_name=sheet_name, index=False)


def convert_csv_to_html():
    """
    Convert CSV files to HTML files.
    """

    print("Converting CSV files to HTML...")

    # Get all CSV files in the current directory
    csv_files = [file for file in os.listdir(dpspth.sbs_class_vocab_dir) if file.endswith('.csv')]

    for csv_file in csv_files:
        csv_path = os.path.join(dpspth.sbs_class_vocab_dir, csv_file)

        df = pd.read_csv(csv_path).fillna("").sort_values(by='cl.')

        # Convert DataFrame to HTML table
        html_table = df.to_html(index=False, classes='sortable')

        # Extract class number from filename
        class_number = os.path.splitext(csv_file)[0].split('-')[-1]

        # HTML template for the table
        html_template = Template('''
            <!DOCTYPE html>
            <html>
            <head>
            <title>Vocabulary List for $class_number</title>
            <style>
            table {
                width: 100%;
                word-wrap: break-word;
            }
            th {
                text-align: center;
            }
            </style>
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.31.1/js/jquery.tablesorter.min.js"></script>
            <script>
            $(document).ready(function() {
                $('table.sortable').tablesorter();
            });
            </script>
            </head>
            <body>
            <h1>Vocabulary List for $class_number</h1>
            <a href="https://sasanarakkha.github.io/study-tools/pali-class/vocab/index-vocab.html">go to index of vocabulary related to each class</a>
            <br>
            <br>
            $table
            </body>
            </html>
        ''')

        # Substitute the class number placeholder with the actual class number
        html_content = html_template.safe_substitute(table=html_table, class_number=class_number)

        # Generate output HTML file name
        html_output_file = os.path.splitext(csv_file)[0] + '.html'

        # Write the HTML content to the file in the same directory
        html_output_path = os.path.join(dpspth.pali_class_vocab_html_dir, html_output_file)
        with open(html_output_path, 'w') as file:
            file.write(html_content)

        print(f"HTML file '{html_output_file}' created successfully.")


if __name__ == "__main__":
    main()

