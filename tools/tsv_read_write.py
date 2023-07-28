"""Modules for reading and writing TSV files."""

import csv
from typing import List


def read_tsv(file_path):
    with open(file_path, "r") as file:
        reader = csv.reader(file, delimiter='\t')
        data = []
        for row in reader:
            data.append(row)
        return data


def read_tsv_dict(file_path):
    with open(file_path, "r") as file:
        reader = csv.DictReader(file, delimiter='\t')
        data = []
        for row in reader:
            data.append(dict(row))
        return data


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def read_tsv_dot_dict(file_path):
    with open(file_path, "r") as file:
        reader = csv.DictReader(file, delimiter='\t')
        data = []
        for row in reader:
            row = dotdict(row)
            data.append(row)
    return data


def write_tsv_dot_dict(file_path, data):
    with open(file_path, "w", newline='') as file:
        writer = csv.DictWriter(
            file, fieldnames=data[0].keys(), delimiter='\t')
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def write_tsv_list(
        file_path: str,
        header: List[str],
        data: List[List[str]]) -> None:
    with open(file_path, "w", newline="") as file:
        writer = csv.writer(file, delimiter="\t")
        if header:
            writer.writerow(header)
        for row in data:
            if row[0]:
                writer.writerow(row)
