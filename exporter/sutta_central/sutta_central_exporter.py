#!/usr/bin/env python3

"""
Export DPD for Sutta Central in the following format:
A list of dictionaries containing basic definitions
1. pos. 2. meaning html 3. construction
```
[
  {
    "entry": "ṭhātabbaṃ",
    "definition": [
      "ptp. <b>should stand; should wait</b>; lit. to be stood [√ṭhā + tabba]",
      "ptp. <b>should remain (in); should stay (in)</b>; lit. to be stood [√ṭhā + tabba]"
    ]
  },
]
```
"""

from json import dump
from rich import print
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup

from tools.cst_sc_text_sets import make_sc_text_set
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.pali_text_files import sc_texts
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class SuttaCentralExporter:
    pth: ProjectPaths = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)

    sc_books_list = [
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
        "kn8",
        "kn9",
    ]

    # sc_books_list: list[str] = []
    sc_word_set: set[str]

    lookup_db: list[Lookup] = []
    lookup_dict: dict[str, Lookup] = {}

    headword_db: list[DpdHeadword] = []
    headword_dict: dict[int, DpdHeadword] = {}

    sc_dict: dict[str, list[tuple[str, str]]] = {}
    sc_dict_compiled: list[dict] = []
    no_entries_list: list[str] = []

    def __init__(self):
        pr.title("exporting for sutta central")
        # self.make_sc_books_list()

        self.sc_word_set = make_sc_text_set(
            self.pth,
            self.sc_books_list,
            niggahita="ṃ",
            add_hyphenated_parts=True,
        )
        self.sc_word_set = set(word for word in self.sc_word_set if word.strip())

        self.make_lookup_dict()
        self.make_headwords_dict()
        self.make_sc_dict()
        self.compile_sc_dict()
        # self.print_sc_dict()
        self.save_sc_dict()
        # self.print_no_entries()

    def make_sc_books_list(self):
        """A list of SC books which have associated text files."""
        pr.green("making sc books list")
        for book, files in sc_texts.items():
            if files:
                self.sc_books_list.append(book)
        pr.yes(len(self.sc_books_list))

    def make_lookup_dict(self):
        """Make a dict of the lookup table for quick reference."""

        pr.green("making lookup dict")

        self.lookup_db = self.db_session.query(Lookup).all()
        for i in self.lookup_db:
            self.lookup_dict[i.lookup_key] = i

        pr.yes(len(self.lookup_dict))

    def make_headwords_dict(self):
        """Make a dict of the headwords table for quick reference."""

        pr.green("making headwords dict")

        headword_db = self.db_session.query(DpdHeadword).all()
        self.headword_db = sorted(headword_db, key=lambda x: pali_sort_key(x.lemma_1))
        for i in self.headword_db:
            self.headword_dict[i.id] = i

        pr.yes(len(self.headword_dict))

    def make_sc_dict(self):
        """Match words in SC texts to dictionary headwords."""
        pr.green("making sc dict")

        for word in self.sc_word_set:
            if word in self.lookup_dict:
                self.sc_dict[word] = []
                lookup_entry = self.lookup_dict[word]
                if lookup_entry.headwords:
                    ids = lookup_entry.headwords_unpack
                    for id in ids:
                        if id in self.headword_dict:
                            headword = self.headword_dict[id]
                            entry: str = self.make_sc_headword_entry(headword)
                            self.sc_dict[word].append((headword.lemma_1, entry))
                if lookup_entry.deconstructor:
                    deconstructions = lookup_entry.deconstructor_unpack
                    for deconstruction in deconstructions:
                        self.sc_dict[word].append(("", deconstruction))
                        break  # only one

        pr.yes(len(self.sc_dict))

    def make_sc_headword_entry(self, headword: DpdHeadword) -> str:
        """Take a headword and return string"""
        entry = []
        entry.append(headword.pos)
        entry.append(". ")
        entry.append(headword.meaning_combo_html)
        if headword.construction_summary:
            entry.append(" [")
            entry.append(headword.construction_summary)
            entry.append("]")

        return "".join(entry)

    def print_sc_dict(self):
        for count, i in enumerate(self.sc_dict):
            if count > 100:
                break
            else:
                print(i, self.sc_dict[i])
        print(len(self.sc_dict))

    def compile_sc_dict(self):
        """Compile the entries into SC format."""

        pr.green("compiling sc dict")

        # sc_word_set_sorted = pali_list_sorter(self.sc_word_set)
        sc_word_set_sorted = sorted(self.sc_word_set)

        for word in sc_word_set_sorted:
            entries = self.sc_dict.get(word, None)
            if entries:
                entries_sorted = sorted(entries, key=lambda x: pali_sort_key(x[0]))
                sc_entry = {"entry": self.flip(word), "definition": []}
                for entry in entries_sorted:
                    headword, definition = entry
                    if headword:
                        sc_entry["definition"].append(
                            f"{self.flip(headword)}: {self.flip(definition)}"
                        )
                        # sc_entry["definition"].append(definition)
                    else:
                        sc_entry["definition"].append(self.flip(definition))
                self.sc_dict_compiled.append(sc_entry)
            else:
                self.no_entries_list.append(word)

        pr.yes(len(self.sc_dict_compiled))

    def flip(self, text: str):
        """Sutta Central uses `ṁ` instead of `ṃ`."""
        if "ṃ" in text:
            return text.replace("ṃ", "ṁ")
        else:
            return text

    def print_no_entries(self):
        for i in self.no_entries_list:
            print(i)
        print(len(self.no_entries_list))

    def save_sc_dict(self):
        """Save to JSON."""

        pr.green("saving sc dict")
        with open("exporter/sutta_central/sc_dict.json", "w") as f:
            dump(self.sc_dict_compiled, f, ensure_ascii=False, indent=2)
        pr.yes("OK")


def main():
    pr.tic()
    SuttaCentralExporter()
    pr.toc()


if __name__ == "__main__":
    main()
