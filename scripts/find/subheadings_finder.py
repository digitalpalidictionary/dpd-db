#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Find headings and subheadings which
1. Only occur once.
2. Have no examples
3. Do note have source_1 = "1"
"""

from json import load
import re

from bs4 import BeautifulSoup
from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.pali_text_files import cst_texts

mula_books = [
    "vin1",
    "vin2",
    "vin3",
    "vin4",
    "vin5",
    "dn1",
    "dn2",
    "dn3",
    "mn1",
    "mn2",
    "mn3",
    "sn1",
    "sn2",
    "sn3",
    "sn4",
    "sn5",
    "an1",
    "an2",
    "an3",
    "an4",
    "an5",
    "an6",
    "an7",
    "an8",
    "an9",
    "an10",
    "an11",
    "kn1",
    "kn2",
    "kn3",
    "kn4",
    "kn5",
    "kn6",
    "kn7",
    "kn8",
    "kn9",
    "kn10",
    "kn11",
    "kn12",
    "kn13",
    "kn14",
    "kn15",
    "kn16",
    "kn17",
    "kn18",
    "kn19",
    "kn20",
]


class SubheadingsFinder:
    def __init__(self):
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)

        self.cst_freq_dict: dict[str, int]

        self.single_occurrence_set: set[str] = set()
        self.make_single_occurrence_set()
        print(len(self.single_occurrence_set))

        self.headings_set: set[str] = set()
        self.make_headings_set()
        print(len(self.headings_set))

        self.single_occurrence_headings_set: set[str] = self.headings_set.intersection(
            self.single_occurrence_set
        )
        print(len(self.single_occurrence_headings_set))

        self.add_to_db()

    def make_single_occurrence_set(self):
        with open(self.pth.cst_freq_json, "r") as f:
            self.cst_freq_dict = load(f)

        for word, count in self.cst_freq_dict.items():
            if count == 1:
                self.single_occurrence_set.add(word)

    def make_soup(self, file):
        filename = file.replace(".txt", ".xml")

        with open(self.pth.cst_xml_dir.joinpath(filename), "r", encoding="UTF-16") as f:
            xml = f.read()
        return BeautifulSoup(xml, "xml")

    def make_subheadings(self, soup):
        for chapter_tag in soup.find_all("head", attrs={"rend": "chapter"}):
            text = chapter_tag.get_text(strip=True).lower()
            text = re.sub("^.+ ", "", text)
            self.headings_set.add(text)

        for subhead_tag in soup.find_all("p", attrs={"rend": "subhead"}):
            text = subhead_tag.get_text(strip=True).lower()
            text = re.sub("^.+ ", "", text)
            self.headings_set.add(text)

    def make_headings_set(self):
        for book, files in cst_texts.items():
            if book in mula_books:
                for file in files:
                    soup = self.make_soup(file)
                    self.make_subheadings(soup)

    def add_to_db(self):
        for i in self.single_occurrence_headings_set:
            result: Lookup | None = (
                self.db_session.query(Lookup).filter(Lookup.lookup_key == i).first()
            )
            if result:
                headword_ids = result.headwords_unpack
                if len(headword_ids) == 1:
                    headword_id = headword_ids[0]
                    headword: DpdHeadword | None = (
                        self.db_session.query(DpdHeadword)
                        .filter(DpdHeadword.id == headword_id)
                        .first()
                    )
                    if headword:
                        if headword.source_1 == "":
                            headword.source_1 = "-"
                            pr.info(f"{headword.lemma_1} updated")
                        else:
                            pr.error(f"{headword.lemma_1} source not empty")
                    else:
                        pr.error(f"'{result.lookup_key}' has no headword!")
                if len(headword_ids) > 1:
                    pr.error(f"'{result.lookup_key}' has two headwords!")

        # self.db_session.commit()


if __name__ == "__main__":
    finder = SubheadingsFinder()
