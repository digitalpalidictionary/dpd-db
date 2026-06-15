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
from typing import ClassVar

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.configger import config_test
from tools.cst_sc_text_sets import make_sc_text_set
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr

DEBUG = False


class SuttaCentralExporter:
    sc_books_list: ClassVar[list[str]] = [
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

    def __init__(self) -> None:
        pr.yellow_title("exporting for sutta central")

        self.pth = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)

        self.lookup_dict: dict[str, Lookup] = {}
        self.headword_dict: dict[int, DpdHeadword] = {}
        self.sc_dict: dict[str, list[tuple[str, str]]] = {}
        self.sc_dict_compiled: list[dict] = []
        self.no_entries_list: list[str] = []

        self.sc_word_set = make_sc_text_set(
            self.pth,
            self.sc_books_list,
            niggahita="ṃ",
            add_hyphenated_parts=True,
        )
        self.sc_word_set = {word for word in self.sc_word_set if word.strip()}

        self.make_lookup_dict()
        self.make_headwords_dict()
        self.make_sc_dict()
        self.compile_sc_dict()
        self.save_sc_dict()
        if DEBUG:
            self.print_sc_dict()
            self.print_no_entries()

    def make_lookup_dict(self) -> None:
        """Make a dict of the lookup entries for the SC text words."""

        pr.green_tmr("making lookup dict")

        chunk_size = 900
        word_list = list(self.sc_word_set)
        for start in range(0, len(word_list), chunk_size):
            chunk = word_list[start : start + chunk_size]
            for i in (
                self.db_session.query(Lookup).filter(Lookup.lookup_key.in_(chunk)).all()
            ):
                self.lookup_dict[i.lookup_key] = i

        pr.yes(len(self.lookup_dict))

    def make_headwords_dict(self) -> None:
        """Make a dict of the headwords table for quick reference."""

        pr.green_tmr("making headwords dict")

        for i in self.db_session.query(DpdHeadword).all():
            self.headword_dict[i.id] = i

        pr.yes(len(self.headword_dict))

    def make_sc_dict(self) -> None:
        """Match words in SC texts to dictionary headwords."""
        pr.green_tmr("making sc dict")

        for word in self.sc_word_set:
            if word in self.lookup_dict:
                self.sc_dict[word] = []
                lookup_entry = self.lookup_dict[word]
                if lookup_entry.headwords:
                    ids = lookup_entry.headwords_unpack
                    for headword_id in ids:
                        if headword_id in self.headword_dict:
                            headword = self.headword_dict[headword_id]
                            entry: str = self.make_sc_headword_entry(headword)
                            self.sc_dict[word].append((headword.lemma_1, entry))
                if lookup_entry.deconstructor:
                    deconstructions = lookup_entry.deconstructor_unpack
                    if deconstructions:
                        self.sc_dict[word].append(("", deconstructions[0]))

        pr.yes(len(self.sc_dict))

    def make_sc_headword_entry(self, headword: DpdHeadword) -> str:
        """Take a headword and return string"""
        entry = f"{headword.pos}. {headword.meaning_combo_html}"
        if headword.construction_summary:
            entry += f" [{headword.construction_summary}]"
        return entry

    def print_sc_dict(self) -> None:
        for count, i in enumerate(self.sc_dict):
            if count > 100:
                break
            else:
                pr.white(f"{i} {self.sc_dict[i]}")
        pr.white(str(len(self.sc_dict)))

    def compile_sc_dict(self) -> None:
        """Compile the entries into SC format."""

        pr.green_tmr("compiling sc dict")

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
                    else:
                        sc_entry["definition"].append(self.flip(definition))
                self.sc_dict_compiled.append(sc_entry)
            else:
                self.no_entries_list.append(word)

        pr.yes(len(self.sc_dict_compiled))

    def flip(self, text: str) -> str:
        """Sutta Central uses `ṁ` instead of `ṃ`."""
        return text.replace("ṃ", "ṁ")

    def print_no_entries(self) -> None:
        for i in self.no_entries_list:
            pr.white(i)
        pr.white(str(len(self.no_entries_list)))

    def save_sc_dict(self) -> None:
        """Save to JSON."""

        pr.green_tmr("saving sc dict")
        with self.pth.sc_pli2en_dpd_json.open("w", encoding="utf-8") as f:
            dump(self.sc_dict_compiled, f, ensure_ascii=False, indent=2)
        pr.yes("OK")


def main() -> None:
    pr.tic()

    if not config_test("exporter", "make_sutta_central", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    SuttaCentralExporter()
    pr.toc()


if __name__ == "__main__":
    main()
