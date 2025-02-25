import csv
from pathlib import Path
from bs4 import BeautifulSoup
from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths
pth = ProjectPaths()


def make_soup(xml_file_path):
    with open(xml_file_path, "r", encoding="utf-16") as f:
        xml_content = f.read()
    soup = BeautifulSoup(xml_content, "xml")
    return soup


def extract_sutta_data(book_list, output_tsv, extract_x_data):
    all_extracted_data = []

    for file_string in book_list:
        file_list = cst_texts[file_string]

        for file_path in file_list:
            file_path = Path(file_path)
            file_path = pth.cst_xml_dir / file_path.with_suffix(".xml")
            soup = make_soup(file_path)
            extracted_data = extract_x_data(soup)
            if extracted_data:
                all_extracted_data.extend(extracted_data)

    if all_extracted_data:
        with open(output_tsv, "w", newline="", encoding="utf-8") as tsv_file:
            fieldnames = all_extracted_data[0].keys()
            writer = csv.DictWriter(tsv_file, fieldnames=fieldnames, delimiter="\t", quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for data in all_extracted_data:
                writer.writerow(data)
        print(f"Data saved to {output_tsv}")
