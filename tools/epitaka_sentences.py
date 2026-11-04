"""Optional context sources for Pass1 Auto prompts: ePitaka sentence pairs
(Pāḷi + English, per CST book) and PEU (Pali English Ultimate) entries.

Both sources may be absent (the contributor server has neither), so every
reader returns an empty result instead of raising."""

import json
import re
import sqlite3
from bisect import bisect_left
from collections import defaultdict
from functools import cache
from pathlib import Path

from tools.clean_machine import clean_machine
from tools.paths import ProjectPaths

EpitakaSentence = tuple[str, str]  # (pali, english)


def _connect_ro(db_path: Path) -> sqlite3.Connection:
    # ePitaka's own app may hold these files open; read-only never writes.
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _sentence_words(pali: str) -> list[str]:
    """Words of one sentence, cleaned the same way as make_cst_text_list,
    so every CST word form finds its sentence."""

    text = re.sub(r"\(.+?\)", "", pali)
    text = clean_machine(text, remove_hyphen=False, show_errors=False)
    words: list[str] = []
    for word in text.split():
        if "-" in word:
            words.append(word.replace("-", ""))
            words.extend(part for part in word.split("-") if part)
        else:
            words.append(word)
    return words


def epitaka_word_dict(
    cst_files: list[str],
    pali_db_path: Path | None = None,
    english_db_path: Path | None = None,
) -> dict[str, list[EpitakaSentence]]:
    """Map every word in the given CST files (stems like `s0506m.mul`) to the
    ePitaka sentences it occurs in, in text order, each sentence once."""

    pth = ProjectPaths(create_dirs=False)
    pali_db_path = pali_db_path or pth.epitaka_db_path
    english_db_path = english_db_path or pth.epitaka_en_db_path
    if not pali_db_path.exists() or not english_db_path.exists() or not cst_files:
        return {}

    conn = _connect_ro(pali_db_path)
    try:
        conn.execute("ATTACH DATABASE ? AS en", (f"file:{english_db_path}?mode=ro",))
        placeholders = ",".join("?" for _ in cst_files)
        rows = conn.execute(
            f"""
            SELECT s.pali, COALESCE(e.translation, '')
            FROM books b
            JOIN sentences s ON s.book_id = b.book_id
            LEFT JOIN en.sentences e
              ON e.book_id = s.book_id
             AND e.para_id = s.para_id
             AND e.line_id = s.line_id
            WHERE b.vri_id IN ({placeholders})
            ORDER BY b.id, s.para_id, s.line_id
            """,
            cst_files,
        ).fetchall()
    finally:
        conn.close()

    word_dict: defaultdict[str, list[EpitakaSentence]] = defaultdict(list)
    for pali, english in rows:
        if not pali:
            continue
        sentence: EpitakaSentence = (pali.strip(), english.strip())
        for word in dict.fromkeys(_sentence_words(pali)):
            word_dict[word].append(sentence)
    return dict(word_dict)


def _peu_clean_key(key: str) -> str:
    # Homonym keys (`sa2`, `sa 1`) and stray punctuation all reduce to letters.
    return re.sub(r"[^a-zāīūṅñṭḍṇḷṃ]", "", key.lower())


@cache
def _load_peu(path: Path) -> tuple[dict[str, list[tuple[str, str]]], list[str]]:
    """Return clean key -> [(headword, entry)] and the sorted clean keys."""

    if not path.exists():
        return {}, []
    raw: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))
    data: defaultdict[str, list[tuple[str, str]]] = defaultdict(list)
    for headword, entry in raw.items():
        clean_key = _peu_clean_key(headword)
        if clean_key:
            data[clean_key].append((headword, entry))
    return dict(data), sorted(data)


def _format_peu(headword: str, entry: str, max_chars: int) -> str:
    entry = re.sub(r"CL=\d+", "", entry)
    entry = re.sub(r"\s+", " ", entry).strip()
    if len(entry) > max_chars:
        entry = entry[:max_chars].rsplit(" ", 1)[0] + " …"
    return f"{headword}: {entry}"


def peu_entries(
    word: str,
    limit: int = 2,
    max_cut: int = 3,
    max_extra: int = 3,
    max_chars: int = 300,
    path: Path | None = None,
) -> list[str]:
    """Find PEU entries for an inflected word.

    Try the exact word, then cut 1..max_cut letters off the end and take the
    headwords that start with what is left and are at most max_extra letters
    longer. The first cut with a hit wins; closest in length to the word first."""

    path = path or ProjectPaths(create_dirs=False).peu_source_json_path
    # _load_peu is cached, so an absent file must not reach it: the file could
    # be installed later in the same session.
    if not path.exists():
        return []
    data, keys = _load_peu(path)
    if not data:
        return []

    if word in data:
        hits = [word]
    else:
        hits = []
        for cut in range(1, max_cut + 1):
            stem = word[:-cut]
            if not stem:
                break
            start = bisect_left(keys, stem)
            end = bisect_left(keys, stem + "￿")
            hits = [k for k in keys[start:end] if len(k) <= len(stem) + max_extra]
            if hits:
                break
        hits.sort(key=lambda k: (abs(len(k) - len(word)), k))

    results: list[str] = []
    for key in hits:
        for headword, entry in data[key]:
            results.append(_format_peu(headword, entry, max_chars))
            if len(results) >= limit:
                return results
    return results
