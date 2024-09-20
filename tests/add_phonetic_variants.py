#!/usr/bin/env python3

"""Find all words with same construction but different lemma_1."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.meaning_construction import clean_construction


class PhoneticVariant():
    def __init__(self, i: DpdHeadword, dict):
        self.lemma_1 = i.lemma_1
        self.lemma_clean = i.lemma_clean
        self.meaning = i.meaning_1
        self.pos = i.pos
        self.construction = i.construction_line1
        self.construction_clean = clean_construction(i.construction)
        self.key = f"{self.construction_clean}, {self.pos}"


class DictEntry():
    def __init__(self, var: PhoneticVariant) -> None:
        """Initialize the dict_entry."""
        self.key = f"{var.construction_clean}, {var.pos}"
        self.variants: list[PhoneticVariant] = [var]
        self.headwords: list[str] = [var.lemma_1]
        self.headwords_count = 1
        self.headwords_clean: set[str] = set([var.lemma_clean])
        self.headwords_clean_count = 1
        self.meanings_set: set[str] = set([var.meaning])
        self.meanings_count = 1


def dict_entry_update(dict, var: PhoneticVariant) -> dict:
    """Initalize or update the dict_entry."""
    
    if not dict.get(var.key):
        dict[var.key] = DictEntry(var)
        return dict
    else:
        dict_entry = dict.get(var.key)
        dict_entry.variants += [var]
        dict_entry.headwords += [var.lemma_1]
        dict_entry.headwords_count = len(dict_entry.headwords)
        dict_entry.headwords_clean.add(var.lemma_clean)
        dict_entry.headwords_clean_count = len(dict_entry.headwords_clean)
        dict_entry.meanings_set.add(var.meaning)
        dict_entry.meanings_count = len(dict_entry.meanings_set)
        return dict


def dict_entry_printer(counter, i: DictEntry) -> None:
    """Print out the dict entry"""
    print(f"{counter} {i.key}")
    print(f"{'headwords':<40}{i.headwords} {i.headwords_count}")
    print(f"{'headwords_clean':<40}{i.headwords_clean} {i.headwords_clean_count}")
    for var in i.variants:
        print(f"{var.lemma_1:<40}[cyan]{var.pos:<10}[green]{var.meaning[:49]:<50}[white]{var.construction}")
    print()


def printer(item) -> None:
    print(f"{item.lemma_1:<40}[cyan]{item.pos:<10}[green]{item.meaning[:49]:<50}[white]{item.construction}")


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    dict = {}

    # if construciton_clean not in dict, update dict
    # if constrction_clean in dict, and if lemma_clean not in dict, update dict

    for i in db:
        if i.meaning_1 and i.construction:
            var = PhoneticVariant(i, dict)
            if var.construction_clean:
                dict = dict_entry_update(dict, var)

    counter = 1
    for construction, dict_entry in dict.items():
        if dict_entry.headwords_clean_count > 1:
            dict_entry_printer(counter, dict_entry)
            counter += 1


if __name__ == "__main__":
    main()
