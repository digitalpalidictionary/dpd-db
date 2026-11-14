"""One-off: split the combined Pass1 Auto draft files into one file per part.

    ap       -> tha-ap, thi-ap          (placed by the SuttaCentral and CST text of each part)
    nidd1&2  -> mnd, cnd                (placed by the SuttaCentral and CST text of each part)
    ja       -> ja-1 ... ja-5           (placed by the CST story number)

The drafts hold words from both texts, so a part is checked against both.
A word goes into every new file that holds it, so a word that occurs in two parts
lands in both. For Apadāna and Niddesa a word in neither part is dropped when it
is a fragment cut at SuttaCentral's bold quote tags ("dukkhan" from
"<b>dukkhan</b>ti"), which an older word splitter made and today's does not. Any
other word in neither part is listed, and the script refuses to write until there
are none. For Jātaka a word with no CST story goes to the last part and is counted
as "unplaced".

Run from the repo root. Prints the counts and writes nothing:
    uv run kamma/threads/20261114_contrib_same_word_clash/artifacts/split_drafts.py
Run the daily pull first, so words contributors finished are already deleted.
To write the new files and delete the old ones, add --write.
"""

import io
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path

from gui2.books import sutta_central_books
from tools.clean_machine import clean_machine
from tools.cst_sc_text_sets import make_cst_text_list
from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths

SPLITS: dict[str, list[str]] = {
    "ap": ["tha-ap", "thi-ap"],
    "nidd1&2": ["mnd", "cnd"],
    "ja": ["ja-1", "ja-2", "ja-3", "ja-4", "ja-5"],
}
DATA = Path("gui2/data")
STORY_HEADING = re.compile(r"^(\d+)\. .*jātakaṃ(?:\s*\([^)]*\))?\s*$")

Placer = Callable[[str], list[str]]


def draft_path(book: str) -> Path:
    return DATA / f"pass1_auto_{book}.json"


def read_text(path: Path) -> str:
    # newline='' keeps the file's own line endings
    with io.open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write_text(path: Path, text: str) -> None:
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def text_placer(parts: list[str]) -> Placer:
    """A word belongs to a part when its SuttaCentral text or its CST book has it."""
    part_words: dict[str, set[str]] = {}
    for part in parts:
        source = sutta_central_books[part]
        words = set(source.word_dict)
        words.update(
            make_cst_text_list(source.cst_books, dedupe=True, show_errors=False)
        )
        part_words[part] = words
    return lambda word: [part for part in parts if word in part_words[part]]


def old_splitter_fragments(parts: list[str]) -> set[str]:
    """Words the old splitter made by cutting at a bold tag: "dukkhan", "ti"."""
    fragments: set[str] = set()
    for part in parts:
        for segment in sutta_central_books[part].segment_dict.values():
            fragments.update(clean_machine(segment.pali, show_errors=False).split())
    return fragments


def cst_story_words() -> dict[str, set[int]]:
    """Each word of the Jātaka root text, with the story numbers where it occurs."""
    cst_dir = ProjectPaths().cst_txt_dir
    blocks: dict[int, list[str]] = {}
    current: int | None = None
    for name in cst_texts["kn14"]:
        for line in read_text(cst_dir / name).splitlines():
            heading = STORY_HEADING.match(line.strip())
            if heading:
                current = int(heading.group(1))
                blocks.setdefault(current, [])
            if current is not None:
                blocks[current].append(line)
    words: dict[str, set[int]] = {}
    for number, lines in blocks.items():
        text = re.sub(r"\(.+?\)", "", "\n".join(lines))
        cleaned = clean_machine(text, remove_hyphen=True, show_errors=False)
        for word in cleaned.split():
            words.setdefault(word, set()).add(number)
    return words


def story_placer(parts: list[str]) -> Placer:
    words = cst_story_words()
    ranges = {part: sutta_central_books[part].story_range for part in parts}

    def place(word: str) -> list[str]:
        numbers = words.get(word, set())
        return [
            part
            for part in parts
            if (r := ranges[part]) is not None and any(n in r for n in numbers)
        ]

    return place


def main() -> int:
    write = "--write" in sys.argv[1:]
    orphans_found = False
    pending: list[tuple[Path, str]] = []
    to_delete: list[Path] = []

    for old, parts in SPLITS.items():
        old_path = draft_path(old)
        if not old_path.exists():
            print(f"{old_path}: missing, skipped (already split?)")
            continue
        text = read_text(old_path)
        newline = "\r\n" if "\r\n" in text else "\n"
        draft: dict[str, dict] = json.loads(text)

        place = story_placer(parts) if old == "ja" else text_placer(parts)
        new_drafts: dict[str, dict[str, dict]] = {part: {} for part in parts}
        fragments = set() if old == "ja" else old_splitter_fragments(parts)
        unplaced: list[str] = []
        dropped: list[str] = []
        shared = 0
        for word, data in draft.items():
            homes = place(word)
            if not homes and word in fragments:
                dropped.append(word)
                continue
            if not homes:
                unplaced.append(word)
                if old == "ja":
                    homes = [parts[-1]]
            shared += len(homes) > 1
            for part in homes:
                new_drafts[part][word] = data

        counts = ", ".join(f"{part} {len(new_drafts[part])}" for part in parts)
        print(
            f"{old}: old {len(draft)} -> {counts}; in more than one part {shared}; "
            f"unplaced {len(unplaced)}; bold tag fragments dropped {len(dropped)}"
        )
        placed = set().union(*[set(d) for d in new_drafts.values()])
        if placed != set(draft) - set(dropped) - (
            set() if old == "ja" else set(unplaced)
        ):
            print(f"  COUNT CHECK FAILED for {old}")
            return 1
        if dropped:
            print(f"  first dropped fragments: {dropped[:15]}")
        if unplaced:
            print(f"  words with no home: {unplaced}")
            if old != "ja":
                orphans_found = True

        for part in parts:
            body = json.dumps(new_drafts[part], ensure_ascii=False, indent=4)
            pending.append((draft_path(part), body.replace("\n", newline)))
        to_delete.append(old_path)

    if orphans_found:
        print("Words with no home found. Nothing written.")
        return 1
    if not write:
        print("Dry run. Add --write to write the new files and delete the old ones.")
        return 0
    for path, body in pending:
        write_text(path, body)
        print(f"wrote {path}")
    for path in to_delete:
        path.unlink()
        print(f"deleted {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
