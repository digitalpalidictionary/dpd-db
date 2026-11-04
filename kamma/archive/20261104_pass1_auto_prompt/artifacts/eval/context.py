"""Old and new prompts for every test word (tasks 2.2, 2.3 and 3.1).

G words: the old prompt is the saved one, verbatim. The new prompt gets the
saved SC sentences first, then ePitaka, and the same related headwords as
the saved prompt (looked up again by lemma_1), minus the gold ids.
K words: both prompts are built from today's SC, ePitaka and dpd.db."""

import json
import re
import sys
from functools import cache

from sqlalchemy import select

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from gui2.books import sutta_central_books
from gui2.pass1_context import (
    AllowedValues,
    Sentence,
    book_name,
    build_new_prompt,
    build_old_prompt,
    choose_sentences,
    load_allowed_values,
    related_entry_dict,
    related_headwords,
)
from tools.epitaka_sentences import epitaka_word_dict, peu_entries
from tools.paths import ProjectPaths

sys.path.insert(0, "kamma/threads/20261104_pass1_auto_prompt/artifacts/eval")
from common import EVAL_DIR, cst_file_stems  # type: ignore  # noqa: E402
from saved_prompt import parse_saved_prompt, read_saved_prompt  # type: ignore  # noqa: E402

G_BOOK_CST: dict[str, list[str]] = {"ja": ["kn14"], "cp": ["kn13"]}

db = get_db_session(ProjectPaths().dpd_db_path)


@cache
def allowed() -> AllowedValues:
    return load_allowed_values(db)


@cache
def epitaka(cst_books: tuple[str, ...]) -> dict[str, list[Sentence]]:
    return epitaka_word_dict(cst_file_stems(list(cst_books)))


def old_related_line(hw: DpdHeadword) -> str:
    # Same text as DatabaseManager.get_related_dict_entries.
    return f"lemma_1: {hw.lemma_1}, pos: {hw.pos}, grammar: {hw.grammar}, meaning_1: {hw.meaning_combo}, root_key: {hw.root_key}, root_sign: {hw.root_sign}, root_base: {hw.root_base}, family_root: {hw.family_root}, family_compound: {hw.family_compound}, construction: {hw.construction}, stem: {hw.stem}, pattern: {hw.pattern}"


def words() -> dict[str, list[dict]]:
    return json.loads((EVAL_DIR / "words.json").read_text(encoding="utf-8"))


def g_prompts(entry: dict) -> tuple[str, str, list[Sentence]]:
    word = entry["word"]
    saved = read_saved_prompt(word)
    sc_sentences, related_lines = parse_saved_prompt(saved)
    lemmas = [re.match(r"lemma_1: (.*?), pos: ", line).group(1) for line in related_lines]  # type: ignore[union-attr]
    headwords = [
        hw for lemma in lemmas
        if (hw := db.scalars(select(DpdHeadword).where(DpdHeadword.lemma_1 == lemma)).first())
    ]
    sentences = choose_sentences(sc_sentences, epitaka(tuple(G_BOOK_CST[entry["book"]])).get(word, []))
    new = build_new_prompt(
        word,
        book_name(entry["book"]),
        sentences,
        [related_entry_dict(hw) for hw in headwords],
        peu_entries(word),
        allowed(),
        exclude_ids=set(entry["gold_ids"]),
    )
    return saved, new, sentences


def k_prompts(entry: dict) -> tuple[str, str, list[Sentence]]:
    word = entry["word"]
    book = entry["book_key"]
    sc = sutta_central_books[book].word_dict.get(word, []) if book in sutta_central_books else []
    sc_sentences = [(s.pali, s.english) for s in sc]
    headwords = related_headwords(db, word)
    old = build_old_prompt(word, sc_sentences, list(dict.fromkeys(old_related_line(hw) for hw in headwords)))
    sentences = choose_sentences(sc_sentences, epitaka(tuple(entry["cst_books"])).get(word, []))
    new = build_new_prompt(
        word,
        book_name(book),
        sentences,
        [related_entry_dict(hw) for hw in headwords],
        peu_entries(word),
        allowed(),
    )
    return old, new, sentences
