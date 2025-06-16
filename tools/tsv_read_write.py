# -*- coding: utf-8 -*-
"""Modules for reading and writing TSV files."""

import csv
from pathlib import Path
from typing import NamedTuple


def read_tsv(file_path):
    with open(file_path, "r") as file:
        reader = csv.reader(file, delimiter="\t")
        data = []
        for row in reader:
            data.append(row)
        return data


def read_tsv_dict(file_path):
    with open(file_path, "r") as file:
        reader = csv.DictReader(file, delimiter="\t")
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
        reader = csv.DictReader(file, delimiter="\t")
        data = []
        for row in reader:
            row = dotdict(row)
            data.append(row)
    return data


def write_tsv_dot_dict(file_path, data):
    with open(file_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys(), delimiter="\t")
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def write_tsv_list(file_path: str, header: list[str], data: list[list[str]]) -> None:
    with open(file_path, "w", newline="") as file:
        writer = csv.writer(file, delimiter="\t")
        if header:
            writer.writerow(header)
        for row in data:
            if row[0]:
                writer.writerow(row)


def append_tsv_list(file_path: str, header: list[str], data: list[list[str]]) -> None:
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
        tsv_reader = csv.reader(tsv_file, delimiter="\t")
        headers = next(tsv_reader)  # Skip the header row
        for row in tsv_reader:
            key = row[0]
            if key:  # Check if the key is not empty
                sub_dict = {headers[i]: value for i, value in enumerate(row) if i != 0}
                dict[key] = sub_dict
    return dict


def read_tsv_as_dict_with_different_key(file_path: Path, key_index: int) -> dict:
    dict_result = {}
    with open(file_path) as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter="\t")
        headers = next(tsv_reader)  # Skip the header row
        for row in tsv_reader:
            key = row[key_index]
            if key:  # Check if the key is not empty
                sub_dict = {
                    headers[i]: value for i, value in enumerate(row) if i != key_index
                }
                dict_result[key] = sub_dict
    return dict_result


class TsvTwoColumnReadResult(NamedTuple):
    data: dict[str, str]
    headers: list[str]


def read_tsv_2col_to_dict(
    file_path: Path,
    key_col: int = 0,
    value_col: int = 1,
) -> TsvTwoColumnReadResult:
    """
    Reads a 2-column TSV file into a dictionary.
    Also returns the headers.
    """
    data_dict: dict[str, str] = {}
    try:
        with open(file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            try:
                headers: list[str] = next(reader)  # Read header row
            except StopIteration:
                # Return empty result if file is empty or has no header
                return TsvTwoColumnReadResult(data=data_dict, headers=[])

            for row in reader:
                if len(row) > max(key_col, value_col):
                    key = row[key_col]
                    value = row[value_col]
                    if key:
                        data_dict[key] = value
    except FileNotFoundError:
        # Return empty result if file not found
        return TsvTwoColumnReadResult(data=data_dict, headers=[])
    return TsvTwoColumnReadResult(data=data_dict, headers=headers)


def write_tsv_2col_from_dict(
    file_path: Path,
    data: dict[str, str],
    headers: list[str] | None = None,
) -> None:
    """Writes a dictionary to a 2-column TSV file with headers."""

    if headers and len(headers) != 2:
        raise ValueError("Header must contain exactly two elements")

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        if headers:
            writer.writerow(headers)
        for key in data.keys():
            writer.writerow([key, data[key]])
