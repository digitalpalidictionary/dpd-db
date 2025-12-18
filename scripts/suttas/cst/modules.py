# -*- coding: utf-8 -*-
import csv
import re
from bs4 import BeautifulSoup


def make_soup(xml_file_path):
    with open(xml_file_path, "r", encoding="utf-16") as f:
        xml_content = f.read()
    soup = BeautifulSoup(xml_content, "xml")
    return soup


def write_cst_tsv(output_tsv, cst_data):
    with open(output_tsv, "w", newline="", encoding="utf-8") as tsv_file:
        fieldnames = cst_data[0].keys()
        writer = csv.DictWriter(
            tsv_file, fieldnames=fieldnames, delimiter="\t", quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        for data in cst_data:
            writer.writerow(data)
    print(f"Data saved to {output_tsv}")


def get_sutta_num(x):
    if re.findall(r"\d", x.text.strip()):
        sutta_num = re.sub(r"\.* .+", "", x.text.strip())
    else:
        sutta_num = "-"
    return sutta_num
