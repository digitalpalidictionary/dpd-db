#!/usr/bin/env python3

"""
    saving words for vocab pali class into separate csv and untute them to one xlsx  and combining them into XLSX/HTML outputs.
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
    print("saving all vocab for ipc and bpc")

    # save vocab for HTML
    seen_words = set()  # Track words that have already been added
    total_words_saved = 0 

    # Save words for each class to a separate CSV file
    for sbs_class in range(2, 30):
        filename = os.path.join(dpspth.sbs_class_vocab_dir, f'vocab-class{sbs_class}.csv')
        words_saved = save_words_to_csv(sbs_class, filename, seen_words)
        if words_saved:
            total_words_saved += words_saved

    print(f"Total words saved to all CSVs: {total_words_saved}")

    convert_csv_to_html()

    # Close the session
    db_session.close()


def save_words_to_csv(sbs_class: int, filename: str, seen_words: set) -> int:
    """
    Save words for a specific class to a CSV file.
    :param sbs_class: Class number.
    :param filename: Output CSV file path.
    :param seen_words: Set to track already saved words
    :return: Number of words saved.
    """
    words = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).join(SBS).filter(
        SBS.sbs_class <= sbs_class,
        SBS.sbs_class_anki <= sbs_class
    ).all()

    words_saved = 0  # Counter for words saved in this CSV file
    # seen_words = seen_words or set()

    # Open the CSV file and write the headers
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['pali', 'pos', 'meaning', 'root', 'construction', 'pattern', 'cl.']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Write each word to the CSV file
        for word in words:
            if word.lemma_1 in seen_words:
                continue  # Skip words that have already been added

            seen_words.add(word.lemma_1)  # Mark word as seen

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

            words_saved += 1  # Increment words saved counter

    return words_saved


def convert_csv_to_html():
    """
    Convert CSV files to HTML, separating them into two groups (Beginner and Intermediate Pāli Course).
    """
    csv_files = [file for file in os.listdir(dpspth.sbs_class_vocab_dir) if file.endswith('.csv')]

    # Separate files into two groups
    group1_files = [file for file in csv_files if 2 <= extract_class_number(file) <= 15]
    group2_files = [file for file in csv_files if 16 <= extract_class_number(file) <= 29]


    # Convert each group to HTML
    convert_group_to_html(group1_files, 'vocab_bpc.html', '2-15', 'Beginner Pāli Course')
    convert_group_to_html(group2_files, 'vocab_ipc.html', '16-29', 'Intermediate Pāli Course')


def extract_class_number(filename):
    # Extract the class number from the filename
    # Assumes filename format is 'vocab-class#.csv'
    class_part = filename.split('-')[-1]
    class_number = class_part.split('.')[0].replace('class', '')
    return int(class_number)


def convert_group_to_html(csv_files, output_filename, class_range, title):
    """
    Convert a group of CSV files into a single HTML file.
    :param csv_files: List of CSV file names.
    :param output_filename: Output HTML file name.
    :param class_range: Class range description.
    :param title: HTML title.
    """
    sorted_csv_files = sorted(csv_files, key=extract_class_number)

    html_tables = []

    for csv_file in sorted_csv_files:
        csv_path = os.path.join(dpspth.sbs_class_vocab_dir, csv_file)

        df = pd.read_csv(csv_path).fillna("").sort_values(by='cl.')

        # Convert DataFrame to HTML table
        html_table = df.to_html(index=False, classes='sortable')

        # Extract class number from filename
        class_number = os.path.splitext(csv_file)[0].split('-')[-1]

        # Add heading and table to the list
        html_tables.append(f"<h2>{class_number}</h2>")
        html_tables.append(html_table)

    # HTML template for the tables
    html_template = Template('''
        <!DOCTYPE html>
        <html>
        <head>
        <title>Vocabulary List for $title</title>
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
        <h1>Vocabulary List for $title</h1>
        <br>
        <br>
        $tables
        </body>
        </html>
    ''')

    ## Substitute the class range placeholder with the actual tital
    html_content = html_template.safe_substitute(tables="\n".join(html_tables), title=title)

    # Write the HTML content to the file in the same directory
    html_output_path = os.path.join(dpspth.pali_class_vocab_html_dir, output_filename)
    with open(html_output_path, 'w') as file:
        file.write(html_content)

    print(f"HTML file '{output_filename}' created successfully.")

if __name__ == "__main__":
    main()

