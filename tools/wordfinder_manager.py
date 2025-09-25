#!/usr/bin/env python3

"""Find all the books that a word occurs in."""

import json
import re
from typing import Literal

from rich import print

from tools.pali_text_files import cst_texts, sc_texts
from tools.paths import ProjectPaths

SearchType = Literal["EXACT", "STARTS_WITH", "CONTAINS", "REGEX"]


class WordFinderManager:
    def __init__(self):
        # word being looked for
        self.word: str = ""

        # configurable limit for results
        self.max_results: int = 100

        # text files and books
        self.cst_texts = cst_texts
        self.cst_files: dict[str, str] = {}
        self.sc_texts = sc_texts
        self.sc_files: dict[str, str] = {}
        self.cst_text_to_book_name_converter()
        self.sc_text_to_book_name_converter()

        # file freq
        self.pth = ProjectPaths()
        self.cst_file_freq = self.load_cst_file_freq()

        # results
        self.search_results: list[tuple[str, str, int]] = []

    def cst_text_to_book_name_converter(self):
        for book, files in self.cst_texts.items():
            for file in files:
                file = file.replace(".txt", ".xml")
                self.cst_files[file] = book

    def sc_text_to_book_name_converter(self):
        for book, files in self.sc_texts.items():
            for file in files:
                self.sc_files[file] = book

    def load_cst_file_freq(self):
        with open(self.pth.cst_file_freq) as f:
            return json.load(f)

    def _matches(
        self,
        word: str,
        words: list[str],
        search_type: SearchType,
    ) -> list[str]:
        matches = []
        for w in words:
            if search_type == "EXACT":
                if w == word:
                    matches.append(w)
            elif search_type == "STARTS_WITH":
                if w.startswith(word):
                    matches.append(w)
            elif search_type == "CONTAINS":
                if word in w:
                    matches.append(w)
            elif search_type == "REGEX":
                try:
                    if re.search(word, w):
                        matches.append(w)
                except re.error:
                    pass  # Skip invalid regex
        return matches

    def _order_results_by_cst_texts(
        self, results_dict: dict[str, list[tuple[str, int]]]
    ) -> list[tuple[str, str, int]]:
        """Order results based on the key order in cst_texts."""
        ordered_results = []
        cst_order = list(self.cst_texts.keys())
        for book in cst_order:
            if book in results_dict:
                for word, freq in results_dict[book]:
                    ordered_results.append((book, word, freq))
        return ordered_results

    def search_for(
        self,
        word: str,
        search_type: SearchType = "STARTS_WITH",
        printer: bool = True,
        max_results: int | None = None,
    ) -> None:
        self.word = word
        self.search_results = []
        results_dict: dict[str, list[tuple[str, int]]] = {}
        for file in self.cst_file_freq:
            words_in_file = list(self.cst_file_freq[file].keys())
            matching_words = self._matches(word, words_in_file, search_type)
            for match in matching_words:
                book = self.cst_files.get(file, "unknown")
                freq = self.cst_file_freq[file][match]
                if book not in results_dict:
                    results_dict[book] = []
                results_dict[book].append((match, freq))
        self.search_results = self._order_results_by_cst_texts(results_dict)
        # Reduce to top max_results after sorting
        limit = max_results if max_results is not None else self.max_results
        self.search_results = self.search_results[:limit]
        if printer:
            print(self.format_results(self.search_results))

    def format_results(self, results: list[tuple[str, str, int]]) -> list[str]:
        """Format results as strings for display."""
        return [f"{book}: {word} ({freq})" for book, word, freq in results]

    def terminal_search(self):
        """Simple interactive search using REGEX."""

        print("Enter a word to search (or 'exit' to quit):")
        while True:
            user_input = input("> ").strip()
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            if user_input:
                self.search_for(user_input, "REGEX")
                results = self.format_results(self.search_results)
                if results:
                    print("\n".join(results))
                else:
                    print("No results found.")
            print("\nEnter another word (or 'exit' to quit):")


if __name__ == "__main__":
    manager = WordFinderManager()
    manager.terminal_search()
