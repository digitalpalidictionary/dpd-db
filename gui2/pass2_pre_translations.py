"""English for Pass2Pre's CST examples, from the tipitaka translations db.

The db is translated paragraph by paragraph, so an example sentence gets the
English of the whole paragraph it sits in."""

import re
import sqlite3
from pathlib import Path

from tools.clean_machine import clean_machine
from tools.pali_text_files import cst_texts

NOTE_RE: re.Pattern[str] = re.compile(r"<note>.*?</note>")
TAG_RE: re.Pattern[str] = re.compile(r"<[^>]+>")
BRACKETS_RE: re.Pattern[str] = re.compile(r"\[.*?\]")


def normalise(text: str) -> str:
    """Pāḷi letters and single spaces only."""

    text = NOTE_RE.sub(" ", text)
    # no space: bold tags sit inside words, <hi rend="bold">bhāvanābala</hi>nti
    text = TAG_RE.sub("", text)
    text = BRACKETS_RE.sub(" ", text)
    return " ".join(clean_machine(text, niggahita="ṃ", show_errors=False).split())


class Pass2PreTranslations:
    def __init__(self, db_path: Path, cst_books: list[str]) -> None:
        self.paragraphs: list[tuple[str, str]] = []
        self._cache: dict[str, str | None] = {}

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            for book in cst_books:
                for filename in cst_texts[book]:
                    # s0101a.att.txt -> s0101a_att
                    table = filename.removesuffix(".txt").replace(".", "_")
                    if table not in tables:
                        continue
                    query = (
                        "SELECT pali_text, english_translation "
                        f'FROM "{table}" WHERE pali_text != ""'
                    )
                    for pali, english in conn.execute(query):
                        # padded, so a probe matches whole words only
                        self.paragraphs.append((f" {normalise(pali)} ", english or ""))
        finally:
            conn.close()

    def find_english(self, example: str) -> str | None:
        """The English of the paragraph holding the example, or None if no
        paragraph matches."""

        if example not in self._cache:
            self._cache[example] = self._search(example)
        return self._cache[example]

    def _search(self, example: str) -> str | None:
        words = normalise(example).split()
        # The example search rewrites some text (…pe…, dashes), so a cleaned
        # example may not match word for word; its opening words still do.
        for probe in (" ".join(words), " ".join(words[:8]), " ".join(words[:4])):
            if not probe:
                return None
            for pali, english in self.paragraphs:
                if f" {probe} " in pali:
                    return english
        return None
