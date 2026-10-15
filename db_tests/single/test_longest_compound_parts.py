#!/usr/bin/env python3

"""Suggest a second construction line built from the longest compound parts.

A compound like cātumāsapaccayapavāraṇā has the construction
`catu > cātu + māsa + paccaya + pavāraṇā`, but cātumāsa and paccayapavāraṇā
are both compound headwords, so a second line `cātumāsa + paccayapavāraṇā`
can be added. Only words with `comp` in grammar and no root are checked,
and only those whose construction is still a single line.
"""

import json
import re
from dataclasses import dataclass
from os.path import commonprefix

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.goldendict_tools import open_in_goldendict
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr

comp_re = re.compile(r"\bcomp\b")


@dataclass
class Part:
    raw: str
    left: str
    right: str


def parse_line(line: str) -> list[Part]:
    """Split a construction line into parts, keeping the form before and after `>`."""
    parts: list[Part] = []
    for raw in line.split(" + "):
        forms = [f.strip() for f in re.sub(r"\[.*?\]", "", raw).split(">")]
        parts.append(Part(raw=raw.strip(), left=forms[0], right=forms[-1]))
    return parts


def is_candidate(i: DpdHeadword) -> bool:
    return bool(comp_re.search(i.grammar) and not i.root_key and i.construction)


def build_indexes(
    words: list[DpdHeadword],
) -> tuple[dict[str, set[str]], dict[tuple[str, ...], set[str]]]:
    """Map every lemma and inflected form, and every parsed line 1, to lemma_clean."""
    form_index: dict[str, set[str]] = {}
    parts_index: dict[tuple[str, ...], set[str]] = {}
    for i in words:
        for form in [i.lemma_clean, *i.inflections_list]:
            if form:
                form_index.setdefault(form, set()).add(i.lemma_clean)
        parts = parse_line(i.construction.split("\n")[0])
        if len(parts) >= 2:
            for key in (
                tuple(p.left for p in parts),
                tuple(p.right for p in parts),
            ):
                parts_index.setdefault(key, set()).add(i.lemma_clean)
    return form_index, parts_index


def match_run(
    run: list[Part],
    lemma_clean: str,
    form_index: dict[str, set[str]],
    parts_index: dict[tuple[str, ...], set[str]],
) -> str | None:
    """Return the text a run of parts can be replaced with, or None."""
    # a bracketed sandhi letter like `[r]` has no form; at the edge of a run it
    # would be swallowed and lost from line 2
    if not run[0].right or not run[-1].right:
        return None

    joined = "".join(p.right for p in run)
    joined_matches = bool(form_index.get(joined, set()) - {lemma_clean})
    if joined_matches and joined in lemma_clean:
        # the joined text is what the word actually contains, even if inflected
        return joined

    matches: set[str] = set()
    for key in (tuple(p.left for p in run), tuple(p.right for p in run)):
        matches |= parts_index.get(key, set())
    matches.discard(lemma_clean)
    # spelling variants share a construction, prefer the one the word contains
    in_word = [m for m in matches if m in lemma_clean]
    if in_word:
        return sorted(in_word, key=pali_sort_key)[0]
    if joined_matches:
        return joined
    if not matches:
        return None
    # sandhi hides every variant, so take the one closest to the start of the word
    return min(
        matches,
        key=lambda m: (-len(commonprefix([m, lemma_clean])), pali_sort_key(m)),
    )


def split_cost(segments: list[str]) -> tuple[int, int]:
    """Fewest segments first, then fewest sound-change parts left standing alone."""
    # a lone `ati > aty > acc` in line 2 is worse than `accāraddha + vīriya`
    return len(segments), sum(">" in s for s in segments)


def best_split(
    line: str,
    lemma_clean: str,
    form_index: dict[str, set[str]],
    parts_index: dict[tuple[str, ...], set[str]],
) -> str | None:
    """Return the fewest-parts version of a construction line, or None if no shorter."""
    parts = parse_line(line)
    n = len(parts)
    # best[j] = shortest list of segments covering parts[:j]
    best: list[list[str] | None] = [None] * (n + 1)
    best[0] = []
    for j in range(1, n + 1):
        for i in range(j):
            prev = best[i]
            if prev is None:
                continue
            if j - i == 1:
                segment: str | None = parts[i].raw
            elif j - i == n:
                continue
            else:
                segment = match_run(parts[i:j], lemma_clean, form_index, parts_index)
            if segment is None:
                continue
            candidate = [*prev, segment]
            current = best[j]
            if current is None or split_cost(candidate) < split_cost(current):
                best[j] = candidate
    result = best[n]
    if result is None or len(result) >= n:
        return None
    return " + ".join(result)


def load_exceptions(pth: ProjectPaths) -> list[str]:
    if pth.longest_compound_parts_exceptions_path.exists():
        with open(pth.longest_compound_parts_exceptions_path, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_exceptions(pth: ProjectPaths, exceptions: list[str]) -> None:
    exceptions.sort(key=pali_sort_key)
    with open(pth.longest_compound_parts_exceptions_path, "w", encoding="utf-8") as f:
        json.dump(exceptions, f, ensure_ascii=False, indent=2)


def main() -> None:
    pr.tic()
    print("[bright_yellow]find longer compound parts for constructions")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    words = [i for i in db_session.query(DpdHeadword).all() if is_candidate(i)]
    form_index, parts_index = build_indexes(words)
    exceptions = load_exceptions(pth)

    hits: list[tuple[DpdHeadword, str]] = []
    for i in words:
        if "\n" in i.construction or i.lemma_1 in exceptions:
            continue
        # negatives are left out for now
        if i.construction.startswith("na "):
            continue
        if len(parse_line(i.construction)) < 3:
            continue
        line_2 = best_split(i.construction, i.lemma_clean, form_index, parts_index)
        if line_2:
            hits.append((i, line_2))
    hits.sort(key=lambda h: pali_sort_key(h[0].lemma_1))

    total = len(hits)
    for count, (i, line_2) in enumerate(hits, start=1):
        print()
        print(f"[dark_orange]{count} of {total}")
        print(f"[dark_orange]{'lemma_1':<20}[/dark_orange][white]{i.lemma_1}")
        print(f"[dark_orange]{'construction':<20}[/dark_orange][white]{i.construction}")
        print(f"[dark_orange]{'line 2':<20}[/dark_orange][light_green]{line_2}")
        open_in_goldendict(i.lemma_clean)
        print()
        print(
            "[yellow]a[white]ccept [yellow]e[white]xception "
            "[yellow]q[white]uit or Enter for next: ",
            end="",
        )
        choice = input().strip().lower()
        if choice == "a":
            # the word may have been edited elsewhere (gui2) since the script loaded it
            db_session.refresh(i)
            if "\n" in i.construction:
                print("[red]construction already has a second line, not saved")
                continue
            i.construction = f"{i.construction}\n{line_2}"
            db_session.commit()
            print("[green]saved")
        elif choice == "e":
            exceptions.append(i.lemma_1)
            save_exceptions(pth, exceptions)
        elif choice == "q":
            break

    pr.toc()


if __name__ == "__main__":
    main()
