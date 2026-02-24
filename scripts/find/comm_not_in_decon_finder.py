#!/usr/bin/env python3

"""Find words in commentaries that are not in the lookup table, sorted by frequency."""

import json
import pyperclip
from pathlib import Path
from dataclasses import dataclass, field
from rich import print

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.cst_sc_text_sets import make_cst_text_set
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import write_tsv_list



@dataclass
class FinderData:
    commentray_books = ["dna", "mna", "sna", "ana"]
    pth: ProjectPaths = ProjectPaths()
    frequency_dict: dict[str, int] = field(default_factory=dict)
    lookup_words: set[str] = field(default_factory=set)
    commentary_words: set[str] = field(default_factory=set)
    missing_words: set[str] = field(default_factory=set)
    words_with_freq: dict[str, int] = field(default_factory=dict)
    sorted_results: list[tuple[str, int]] = field(default_factory=list)

def load_combined_frequency(data: FinderData) -> None:
    pr.green("loading frequency files")

    freq_files = [
        # data.pth.bjt_freq_json,
        data.pth.cst_freq_json,
        # data.pth.sc_freq_json,
        # data.pth.sya_freq_json
    ]

    for file_path in freq_files:
        if file_path.exists():
            with open(file_path, "r") as f:
                file_data = json.load(f)
                for word, count in file_data.items():
                    data.frequency_dict[word] = data.frequency_dict.get(word, 0) + count
        else:
            pr.red(f"file not found: {file_path}")

    pr.yes(len(data.frequency_dict))

def get_lookup_words(data: FinderData) -> None:
    pr.green("getting words from lookup table")
    db_session = get_db_session(data.pth.dpd_db_path)
    lookup_db = db_session.query(Lookup.lookup_key).all()
    data.lookup_words = {i.lookup_key for i in lookup_db}
    pr.yes(len(data.lookup_words))

def get_commentary_words(data: FinderData) -> None:
    # make_cst_text_set already has its own pr.green/pr.yes
    data.commentary_words = make_cst_text_set(data.pth, data.commentray_books)

def find_missing_words(data: FinderData) -> None:
    pr.green("finding missing words")
    data.missing_words = data.commentary_words - data.lookup_words
    pr.yes(len(data.missing_words))

def add_frequencies_to_words(data: FinderData) -> None:
    pr.green("adding frequencies to words")
    data.words_with_freq = {word: data.frequency_dict.get(word, 0) for word in data.missing_words}
    pr.yes(len(data.words_with_freq))

def sort_by_frequency(data: FinderData) -> None:
    pr.green("sorting by frequency")
    # Sort by frequency descending, then by word ascending for ties
    data.sorted_results = sorted(data.words_with_freq.items(), key=lambda x: (-x[1], x[0]))
    pr.yes(len(data.sorted_results))

def save_to_tsv(data: FinderData) -> None:
    pr.green("saving to tsv")
    tsv_path = data.pth.temp_dir / "comm_not_in_lookup.tsv"
    header = ["word", "frequency"]
    tsv_data = [[word, str(freq)] for word, freq in data.sorted_results]
    write_tsv_list(str(tsv_path), header, tsv_data)
    pr.yes("ok")
    pr.info(f"saved to: {tsv_path.relative_to(Path.cwd())}")

def run_interactive_loop(data: FinderData) -> None:
    total = len(data.sorted_results)
    print(f"found {total} missing words")
    print("press [blue]enter[/blue] to copy next word, or [blue]q[/blue] to quit")

    for index, (word, freq) in enumerate(data.sorted_results):
        print(f"{index + 1:>5} / {total:<5} [white]{word:<30}[/white] [cyan]{freq:>10}[/cyan]", end=" ", flush=True)
        pyperclip.copy(word)
        user_input = input()
        if user_input.lower() == "q":
            break

def main():
    pr.tic()
    pr.title("commentary words not found in the lookup table")

    data = FinderData()

    load_combined_frequency(data)
    get_lookup_words(data)
    get_commentary_words(data)
    find_missing_words(data)
    add_frequencies_to_words(data)
    sort_by_frequency(data)
    save_to_tsv(data)
    run_interactive_loop(data)

    pr.toc()

if __name__ == "__main__":
    main()
