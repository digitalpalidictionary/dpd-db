# -*- coding: utf-8 -*-
import json
import threading
from pathlib import Path
from typing import Any, Callable, Dict

from gui2.paths import Gui2Paths


def _valid_lists(folder: Path) -> list[dict[str, list[str]]]:
    """One cleaned dict per removed list in the folder.

    A list from a contributor is untrusted: a file that is not a JSON object is
    skipped, and an entry that is not a list of strings is dropped."""
    lists: list[dict[str, list[str]]] = []
    for path in sorted(folder.glob("pass1_auto_removed_*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, ValueError, RecursionError):
            continue
        if not isinstance(raw, dict):
            continue
        lists.append(
            {
                book: words
                for book, words in raw.items()
                if isinstance(book, str)
                and isinstance(words, list)
                and all(isinstance(word, str) for word in words)
            }
        )
    return lists


class Pass1FileManager:
    # NOTE (contributor web server, #215): pass1_auto_{book}.json is a shared,
    # read-modify-written work queue. self._lock is intra-process only, so if two
    # server contributor instances process the SAME book at once their writes can
    # corrupt this file. Current mitigation is operational — assign a different
    # book per contributor. FIX (per-book file lock or atomic os.replace) only if
    # concurrent same-book editing ever actually happens.
    def __init__(self, paths: Gui2Paths):
        self.gui2_data_path = paths.gui2_data_path
        # Set for a contributor: the pass1_auto files are tracked by git, so the
        # server must never edit them. Finished words go to this list instead.
        self.removed_path = paths.pass1_auto_removed_path
        self._lock = threading.Lock()

    def _get_filepath(self, book: str) -> Path:
        return self.gui2_data_path / f"pass1_auto_{book}.json"

    def _list_folder(self) -> Path:
        if self.removed_path is not None:
            return self.removed_path.parent
        return self.gui2_data_path

    def _hidden_words(self, book: str) -> set[str]:
        hidden: set[str] = set()
        for removed in _valid_lists(self._list_folder()):
            hidden.update(removed.get(book, []))
        return hidden

    def finished_words(self, book: str) -> set[str]:
        """Words any contributor finished in this book, read fresh from disk.

        The laptop ignores pulled contributor lists, so it gets an empty set."""
        if self.removed_path is None:
            return set()
        with self._lock:
            return self._hidden_words(book)

    def all_removed_words(self) -> set[str]:
        words: set[str] = set()
        for removed in _valid_lists(self._list_folder()):
            for book_words in removed.values():
                words.update(book_words)
        return words

    def _read_removed(self) -> dict[str, list[str]]:
        if self.removed_path is None or not self.removed_path.exists():
            return {}
        try:
            with self.removed_path.open("r", encoding="utf-8") as f:
                removed = json.load(f)
        except json.JSONDecodeError:
            return {}
        return removed if isinstance(removed, dict) else {}

    def _read_file(self, book: str) -> Dict[str, Any]:
        filepath = self._get_filepath(book)
        if filepath.exists():
            with filepath.open("r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _read_view(self, book: str) -> Dict[str, Any]:
        data = self._read_file(book)
        if self.removed_path is not None:
            hidden = self._hidden_words(book)
            data = {word: v for word, v in data.items() if word not in hidden}
        return data

    def read(self, book: str) -> Dict[str, Any]:
        with self._lock:
            return self._read_view(book)

    def remove(self, book: str, word: str) -> Dict[str, Any]:
        """Remove a finished word and return the book's remaining words.

        The laptop deletes it from the file. A contributor lists it as removed
        and leaves the tracked file as it is."""

        if self.removed_path is None:

            def delete_word(data: Dict[str, Any]) -> Dict[str, Any]:
                data.pop(word, None)
                return data

            return self.update(book, delete_word)

        with self._lock:
            removed = self._read_removed()
            if word not in removed.setdefault(book, []):
                removed[book].append(word)
                self.removed_path.parent.mkdir(parents=True, exist_ok=True)
                # A crash mid-write must not truncate the list: every removed
                # word would then reappear for the contributor.
                tmp_path = self.removed_path.with_name(self.removed_path.name + ".tmp")
                with tmp_path.open("w", encoding="utf-8") as f:
                    json.dump(removed, f, ensure_ascii=False, indent=4, sort_keys=True)
                tmp_path.replace(self.removed_path)
            return self._read_view(book)

    def _refuse_tracked_write(self) -> None:
        if self.removed_path is not None:
            raise PermissionError(
                "The Pass1 Auto files are read-only on the server. Use remove()."
            )

    def write(self, book: str, data: Dict[str, Any]):
        self._refuse_tracked_write()
        with self._lock:
            filepath = self._get_filepath(book)
            with filepath.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    def update(
        self, book: str, update_function: Callable[[Dict[str, Any]], Any]
    ) -> Any:
        self._refuse_tracked_write()
        with self._lock:
            filepath = self._get_filepath(book)
            data = {}
            if filepath.exists():
                try:
                    with filepath.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                except json.JSONDecodeError:
                    # Handle corrupted or empty file
                    pass

            result = update_function(data)

            with filepath.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            return result
