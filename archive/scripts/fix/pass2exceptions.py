"""Audit gui2/data/pass2_exceptions.json for entries that block the only example.

Each exception phrase suppresses any candidate example sentence containing it in
the pass2 preprocessor. An accidentally-added exception can hide the only example
for a headword that still needs one. This script splits every phrase into words,
looks each word up, finds its headwords, and flags words whose headwords still
have no meaning so the offending phrase can be tested and removed. Words kept
during review are recorded in pass2exceptions.json and never shown again.
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass, field

import pyperclip
from pathlib import Path

from rich.console import Console
from sqlalchemy.orm import Session, defer

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from gui2.paths import Gui2Paths
from tools.goldendict_tools import open_in_goldendict
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths

PUNCTUATION = " ,.;:!?\"'“”‘’…«»()[]"
BATCH_SIZE = 900
KEEP_PATH = Path("scripts/fix/pass2exceptions.json")

console = Console()


@dataclass
class HeadwordInfo:
    id: int
    lemma_1: str
    pos: str
    meaning_combo: str
    missing: bool


@dataclass
class WordItem:
    word: str
    phase: int
    headwords: list[HeadwordInfo]
    phrases: set[str] = field(default_factory=set)


def load_exceptions(path: Path) -> set[str]:
    with open(path, "r", encoding="utf-8") as file:
        return set(json.load(file))


def save_exceptions(path: Path, exceptions: set[str]) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            pali_list_sorter(exceptions),
            file,
            indent=4,
            ensure_ascii=False,
        )


def load_kept() -> set[str]:
    try:
        with open(KEEP_PATH, "r", encoding="utf-8") as file:
            return set(json.load(file))
    except FileNotFoundError:
        return set()


def save_kept(kept: set[str]) -> None:
    with open(KEEP_PATH, "w", encoding="utf-8") as file:
        json.dump(pali_list_sorter(kept), file, indent=4, ensure_ascii=False)


def build_word_to_phrases(exceptions: set[str]) -> dict[str, set[str]]:
    word_to_phrases: dict[str, set[str]] = {}
    for phrase in exceptions:
        for raw_word in phrase.split():
            word = raw_word.strip(PUNCTUATION)
            if word:
                word_to_phrases.setdefault(word, set()).add(phrase)
    return word_to_phrases


def chunk(items: list[str], size: int) -> Iterator[list[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def get_word_to_ids(db_session: Session, words: list[str]) -> dict[str, list[int]]:
    word_to_ids: dict[str, list[int]] = {}
    for batch in chunk(words, BATCH_SIZE):
        rows = db_session.query(Lookup).filter(Lookup.lookup_key.in_(batch)).all()
        for row in rows:
            ids = row.headwords_unpack
            if ids:
                word_to_ids[row.lookup_key] = ids
    return word_to_ids


def get_headword_infos(db_session: Session, ids: list[int]) -> dict[int, HeadwordInfo]:
    infos: dict[int, HeadwordInfo] = {}
    for batch in chunk([str(i) for i in ids], BATCH_SIZE):
        int_batch = [int(i) for i in batch]
        rows: list[DpdHeadword] = (
            db_session.query(DpdHeadword)
            .options(
                defer(DpdHeadword.inflections_html),
                defer(DpdHeadword.freq_html),
                defer(DpdHeadword.inflections_sinhala),
                defer(DpdHeadword.inflections_devanagari),
                defer(DpdHeadword.inflections_thai),
                defer(DpdHeadword.freq_data),
            )
            .filter(DpdHeadword.id.in_(int_batch))
            .all()
        )
        for row in rows:
            infos[row.id] = HeadwordInfo(
                id=row.id,
                lemma_1=row.lemma_1,
                pos=row.pos,
                meaning_combo=row.meaning_combo,
                missing=not row.meaning_1,
            )
    return infos


def build_items(
    word_to_phrases: dict[str, set[str]],
    word_to_ids: dict[str, list[int]],
    headword_infos: dict[int, HeadwordInfo],
    kept: set[str],
) -> list[WordItem]:
    items: list[WordItem] = []
    for word, phrases in word_to_phrases.items():
        if word in kept:
            continue
        ids = word_to_ids.get(word, [])
        headwords = [headword_infos[i] for i in ids if i in headword_infos]
        if not headwords:
            continue
        missing = [hw for hw in headwords if hw.missing]
        if not missing:
            continue
        phase = 1 if len(headwords) == 1 else 2
        items.append(
            WordItem(word=word, phase=phase, headwords=missing, phrases=phrases)
        )

    sorted_words = pali_list_sorter([item.word for item in items])
    order = {word: index for index, word in enumerate(sorted_words)}
    items.sort(key=lambda item: (item.phase, order[item.word]))
    return items


def analyse(
    db_session: Session, exceptions: set[str], kept: set[str]
) -> list[WordItem]:
    word_to_phrases = build_word_to_phrases(exceptions)
    word_to_ids = get_word_to_ids(db_session, list(word_to_phrases))
    all_ids = sorted({i for ids in word_to_ids.values() for i in ids})
    headword_infos = get_headword_infos(db_session, all_ids)
    return build_items(word_to_phrases, word_to_ids, headword_infos, kept)


def print_summary(items: list[WordItem], exceptions: set[str]) -> None:
    phase1 = [item for item in items if item.phase == 1]
    phase2 = [item for item in items if item.phase == 2]
    console.print()
    console.print(f"exception phrases:  {len(exceptions)}", style="cyan")
    console.print(f"flagged words:      {len(items)}", style="cyan")
    console.print(f"phase 1 (urgent):   {len(phase1)}", style="yellow")
    console.print(f"phase 2 (mixed):    {len(phase2)}", style="yellow")
    console.print()


def display_item(
    item: WordItem,
    index: int,
    total: int,
    live_phrases: list[str],
) -> None:
    console.print()
    console.print(f"{index}/{total} : {item.word}", style="bold yellow")
    for hw in item.headwords:
        console.print(f"{hw.id} {hw.lemma_1} {hw.pos} {hw.meaning_combo}", style="cyan")
    for number, phrase in enumerate(live_phrases, start=1):
        console.print(f"{number}) {phrase}", style="green")


def run_tui(
    path: Path,
    exceptions: set[str],
    items: list[WordItem],
    kept: set[str],
) -> None:
    total = len(items)
    deleted: set[str] = set()

    for index, item in enumerate(items, start=1):
        live_phrases = [
            phrase for phrase in pali_list_sorter(item.phrases) if phrase not in deleted
        ]
        if not live_phrases:
            continue

        display_item(item, index, total, live_phrases)
        pyperclip.copy(item.word)
        open_in_goldendict(item.word)

        while True:
            answer = console.input(
                r"[dim]\[1-N] delete  \[a] delete all  \[k] keep  \[q] quit:[/dim] "
            ).strip()

            if answer == "q":
                console.print("quitting.", style="red")
                return
            if answer == "k" or answer == "":
                kept.add(item.word)
                save_kept(kept)
                break
            if answer == "a":
                for phrase in live_phrases:
                    exceptions.discard(phrase)
                    deleted.add(phrase)
                save_exceptions(path, exceptions)
                console.print(
                    f"deleted {len(live_phrases)} phrase(s), saved.", style="red"
                )
                break
            if answer.isdigit():
                choice = int(answer)
                if 1 <= choice <= len(live_phrases):
                    phrase = live_phrases[choice - 1]
                    exceptions.discard(phrase)
                    deleted.add(phrase)
                    save_exceptions(path, exceptions)
                    console.print(f"deleted '{phrase}', saved.", style="red")
                    live_phrases = [p for p in live_phrases if p != phrase]
                    if not live_phrases:
                        break
                    for number, remaining in enumerate(live_phrases, start=1):
                        console.print(f"{number}) {remaining}", style="green")
                    continue
            console.print("invalid input.", style="red")

    console.print("\ndone — all flagged words reviewed.", style="bold green")


def main() -> None:
    pth = ProjectPaths()
    gui2_pth = Gui2Paths()
    db_session = get_db_session(pth.dpd_db_path)

    exceptions = load_exceptions(gui2_pth.pass2_exceptions_path)
    kept = load_kept()
    console.print("analysing exceptions...", style="dim")
    items = analyse(db_session, exceptions, kept)
    print_summary(items, exceptions)

    if not items:
        console.print("nothing flagged.", style="dim")
        return

    run_tui(gui2_pth.pass2_exceptions_path, exceptions, items, kept)


if __name__ == "__main__":
    main()
