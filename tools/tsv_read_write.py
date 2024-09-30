"""Modules for reading and writing TSV files."""

import csv
from pathlib import Path
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


def append_tsv_list(
        file_path: str,
        header: List[str],
        data: List[List[str]]) -> None:
    # Check if the file exists and if it's empty
    file_exists = Path(file_path).exists()
    file_empty = False if file_exists else True

    with open(file_path, "a", newline="") as file:
        writer = csv.writer(file, delimiter="\t")
        # Write the header only if the file is empty
        if file_empty and header:
            writer.writerow(header)
        for row in data:
            if row[0]:
                writer.writerow(row)


def read_tsv_as_dict(file_path: Path) -> dict:
    dict = {}
    with open(file_path) as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter='\t')
        headers = next(tsv_reader)  # Skip the header row
        for row in tsv_reader:
            key = row[0]
            if key: # Check if the key is not empty
                sub_dict = {headers[i]: value for i, value in enumerate(row) if i !=  0}
                dict[key] = sub_dict
    return dict


def read_tsv_as_dict_with_different_key(file_path: Path, key_index: int) -> dict:
    dict_result = {}
    with open(file_path) as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter='\t')
        headers = next(tsv_reader)  # Skip the header row
        for row in tsv_reader:
            key = row[key_index]
            if key: # Check if the key is not empty
                sub_dict = {headers[i]: value for i, value in enumerate(row) if i != key_index}
                dict_result[key] = sub_dict
    return dict_result