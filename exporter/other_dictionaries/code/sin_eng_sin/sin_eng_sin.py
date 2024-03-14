#!/usr/bin/env python3
# coding: utf-8

import json

from rich import print

from tools.mdict_exporter import export_to_mdict
from tools.paths import ProjectPaths
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc

class ProgData():
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.data_list: list[dict[str, str]]

        self.bookname = "Sinhala-English English-Sinhala"
        self.author = "University of Colombo School of Computing"
        self.description = """Sinhala-English / English-Sinhala Dictionary"""
        self.website = "https://ucsc.cmb.ac.lk/ltrl/projects/EnSiTip/"





def convert_tab_to_dict(g: ProgData):
    """Open .tab files and make python dict."""

    data_list = []

    # english_sinhala
    with open(g.pth.eng_sin_source_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            line = line.replace("\t\t", "\t")
            try:
                key, value = line.split("\t", 1)
            except ValueError:
                pass
            data_list.append({
                "word": key,
                "definition_html": value,
                "definition_plain": "",
                "synonyms": ""
            })

    # sinhala_english
    with open(g.pth.sin_eng_source_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            line = line.replace("\t\t", "\t")
            try:
                key, value = line.split("\t", 1)
            except ValueError:
                pass
            data_list.append({
                "word": key,
                "definition_html": value,
                "definition_plain": "",
                "synonyms": ""
            })

    g.data_list = data_list


def save_json(g: ProgData):
    """Save as json."""
    print("[green]saving json")
    with open(g.pth.sin_eng_sin_json_path, "w") as file:
        json.dump(g.data_list, file, indent=4, ensure_ascii=False)


def export_golden_dict(g: ProgData):
    """Save as goldendict."""
    print("[green]saving goldendict")

    ifo = ifo_from_opts({
            "bookname": g.bookname,
            "author": g.author,
            "description": g.description,
            "website": g.website,
    })

    export_words_as_stardict_zip(
        g.data_list, ifo, g.pth.sin_eng_sin_gd_path)    # type:ignore


def export_mdict(g: ProgData):
    """Save as mdict"""
    print("[green]saving mdict")

    
    export_to_mdict(
        g.data_list,
        str(g.pth.sin_eng_sin_mdict_path),
        g.bookname,
        g.description,
        h3_header=True)


def main():
    tic()
    print("[bright_yellow]exporting sinhala-english-sinahal to gd, mdict & json")
    print("[green]preparing data")
    g = ProgData()
    convert_tab_to_dict(g)
    save_json(g)
    export_golden_dict(g)
    export_mdict(g)
    toc()


if __name__ == "__main__":
    main()