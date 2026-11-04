"""Shared helpers for the Pass1 Auto prompt test (thread 20261104_pass1_auto_prompt).

Run from the repo root, e.g. `uv run kamma/threads/.../artifacts/eval/coverage.py`."""

import json
from pathlib import Path

from sqlalchemy import select

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from gui2.books import sutta_central_books
from gui2.spelling import SpellingMistakesFileManager
from gui2.variants import VariantReadingFileManager
from tools.cst_sc_text_sets import make_cst_text_list
from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths

EVAL_DIR = Path("kamma/threads/20261104_pass1_auto_prompt/artifacts/eval")

# ePitaka book -> (pass1 book key, CST book codes)
TARGET_BOOKS: dict[str, tuple[str, list[str]]] = {
    "Vv": ("vv", ["kn6"]),
    "Pv": ("pv", ["kn7"]),
    "Ap-i": ("ap", ["kn10"]),
    "Ap-ii": ("ap", ["kn11"]),
    "Bv": ("bv", ["kn12"]),
    "Cp": ("cp", ["kn13"]),
}


def cst_file_stems(cst_books: list[str]) -> list[str]:
    return [f.removesuffix(".txt") for b in cst_books for f in cst_texts[b]]


def all_inflections() -> set[str]:
    db = get_db_session(ProjectPaths().dpd_db_path)
    words: set[str] = set()
    for inflections, api in db.execute(
        select(DpdHeadword.inflections, DpdHeadword.inflections_api_ca_eva_iti)
    ):
        words.update(inflections.split(","))
        words.update(api.split(","))
    words.discard("")
    db.close()
    return words


class MissingChecker:
    """The controller's is_missing() rules, without the GUI."""

    def __init__(self) -> None:
        pth = ProjectPaths()
        self.inflections = all_inflections()
        self.sandhi_ok = set(pth.decon_checked.read_text(encoding="utf-8").splitlines())
        self.variants = VariantReadingFileManager().variants_dict
        self.spelling = SpellingMistakesFileManager().spelling_mistakes_dict

    def auto_keys(self, book_key: str) -> set[str]:
        path = Path(f"gui2/data/pass1_auto_{book_key}.json")
        if not path.exists():
            return set()
        return set(json.loads(path.read_text(encoding="utf-8")))

    def is_missing(self, word: str, auto_keys: set[str]) -> bool:
        return (
            word not in self.inflections
            and word not in self.sandhi_ok
            and word not in auto_keys
            and word not in self.variants
            and word not in self.spelling
        )

    def missing_words(self, book_key: str, cst_books: list[str]) -> list[str]:
        auto = self.auto_keys(book_key)
        words = [
            w for w in make_cst_text_list(cst_books, dedupe=True) if self.is_missing(w, auto)
        ]
        if book_key in sutta_central_books:
            seen = set(words)
            for w in sutta_central_books[book_key].word_dict:
                if w not in seen and self.is_missing(w, auto):
                    words.append(w)
                    seen.add(w)
        return words
