"""Pass2x "in commentary" — stage 1 data-proof TUI (read-only).

Simplest version of the pipeline:

1. Collect every word in the ``commentary`` column of ``dpd_headwords``.
2. Keep only words that are an inflected form (``inflections_list_all``) of a
   headword that still needs a sutta example (``is_missing_sutta_example``).
3. For each kept word, pull the Pāḷi paragraphs it appears in (with English)
   from the Tipiṭaka translations database, with the word bolded.

No database writes, no Flet, no persistence — this exists to validate match
quality before any GUI is built. See
``kamma/threads/20260616_pass2x_in_commentary/spec.md``.

NOTE: the deconstructor/compound lookup (a commentary word that is only a
sandhi/compound in the lookup table, resolved via its component words) is
deliberately OMITTED for now to keep this simple. Re-activate it later — the
logic lives in ``DatabaseManager.get_headwords`` /
``get_headwords_from_deconstructor``. The known-variant and spelling-mistake
exclusions (used in Pass2pre) are likewise left out for now.
"""

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session, defer

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from gui2.paths import Gui2Paths
from gui2.pass2x.in_commentary_exceptions import InCommentaryExceptions
from tools.clean_machine import clean_machine
from tools.cst_book_translator import from_cst_filename
from tools.paths import ProjectPaths
from tools.printer import printer as pr

# how many example paragraphs to keep per word
EXAMPLE_CAP: int = 5
# truncate each example's Pāḷi / English to this many chars in the TSV
EXAMPLE_TRUNC: int = 250
# how many resolved candidates to print in detail
DISPLAY_LIMIT: int = 15
# numbered step TSVs land here for live inspection
OUTPUT_DIR: Path = Path("gui2/pass2x/data")

PALI_LETTERS: str = "a-zāīūṅñṭḍṇḷṃṁ"
SOURCE_PREFIX_RE: re.Pattern[str] = re.compile(r"^\s*\([^)]*\)\s*")
HTML_TAG_RE: re.Pattern[str] = re.compile(r"<[^>]+>")
ANSI_BOLD: str = "\033[1m"
ANSI_RESET: str = "\033[0m"


@dataclass
class Example:
    source: str
    paranum: str
    pali_raw: str
    english: str
    word: str
    book_name: str = ""
    is_commentary: bool = False


@dataclass
class CommentarySource:
    """The commentary entry a word was first harvested from."""

    lemma_1: str
    commentary: str


def write_tsv(rows: list[dict], path: Path) -> None:
    """Write a list of dicts as a TSV (header from first row's keys)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    headers = list(rows[0].keys())
    lines = ["\t".join(headers)]
    for row in rows:
        lines.append(
            "\t".join(
                str(row.get(h, "")).replace("\t", " ").replace("\n", " ")
                for h in headers
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- step 1: harvest words from the commentary column ---


def _words_from_commentary(commentary: str) -> list[str]:
    """Clean a single commentary value into a list of Pāḷi words.

    Strips the leading ``(CODE)`` source prefix, then defers to
    ``clean_machine`` (which already removes ``<b>`` tags, parens, punctuation
    and normalises niggahita to ``ṃ``). Hyphenated forms contribute both the
    whole token and its parts.
    """
    text = SOURCE_PREFIX_RE.sub("", commentary)
    cleaned = clean_machine(text, niggahita="ṃ", remove_hyphen=False, show_errors=False)
    words: list[str] = []
    for token in cleaned.split():
        token = token.strip("-")
        if not token:
            continue
        words.append(token)
        if "-" in token:
            words.extend(part for part in token.split("-") if part)
    return words


def harvest_commentary_words(
    db_session: Session,
) -> tuple[set[str], dict[str, CommentarySource], int]:
    """Return the deduped word set plus, for each word, the first commentary
    entry it was harvested from (its provenance)."""
    rows = (
        db_session.query(
            DpdHeadword.lemma_1,
            DpdHeadword.commentary,
        )
        .filter(DpdHeadword.commentary != "")
        .filter(DpdHeadword.commentary != "-")
        .all()
    )
    words: set[str] = set()
    word_source: dict[str, CommentarySource] = {}
    for lemma_1, commentary in rows:
        for word in _words_from_commentary(commentary):
            words.add(word)
            if word not in word_source:
                word_source[word] = CommentarySource(lemma_1, commentary)
    return words, word_source, len(rows)


# --- step 2/3: map inflections of incomplete headwords -> headword ---


def needs_commentary_example(headword: DpdHeadword) -> bool:
    """Incomplete for Pass2x purposes: the headword has **neither** a
    ``meaning_1`` **nor** a ``source_1`` — both must be empty to count. A
    headword with either one is treated as already done and excluded.
    """
    return not headword.meaning_1 and not headword.source_1


def build_inflection_map(db_session: Session) -> dict[str, list[DpdHeadword]]:
    """Map each inflected form of every incomplete headword to that headword."""
    headwords = (
        db_session.query(DpdHeadword)
        .options(
            defer(DpdHeadword.inflections_html),
            defer(DpdHeadword.freq_html),
            defer(DpdHeadword.inflections_sinhala),
            defer(DpdHeadword.inflections_devanagari),
            defer(DpdHeadword.inflections_thai),
            defer(DpdHeadword.freq_data),
        )
        .all()
    )
    mapping: dict[str, list[DpdHeadword]] = {}
    for headword in headwords:
        if needs_commentary_example(headword):
            for form in headword.inflections_list_all:
                mapping.setdefault(form, []).append(headword)
    return mapping


# --- step 4: translation-sentence sourcing ---


def _clean_for_match(pali_text: str) -> set[str]:
    stripped = HTML_TAG_RE.sub(" ", pali_text)
    return set(clean_machine(stripped, niggahita="ṃ", show_errors=False).split())


def _strip_html(pali_text: str) -> str:
    return HTML_TAG_RE.sub("", pali_text).strip()


def _mark_word(pali_raw: str, word: str, open_tag: str, close_tag: str) -> str:
    """Wrap whole-word occurrences of ``word`` (niggahita-flexible) in tags."""
    flexible = re.sub("[ṃṁ]", "[ṃṁ]", re.escape(word))
    pattern = re.compile(
        rf"(?<![{PALI_LETTERS}])({flexible})(?![{PALI_LETTERS}])",
        re.IGNORECASE,
    )
    return pattern.sub(rf"{open_tag}\1{close_tag}", pali_raw)


@dataclass
class SearchResult:
    examples: dict[str, list[Example]]
    total_hits: dict[str, int] = field(default_factory=dict)
    rows_scanned: int = 0


def find_examples_for_candidates(
    translation_db_path, candidates: set[str], cap: int = EXAMPLE_CAP
) -> SearchResult:
    """Single pass over every translation table, collecting up to ``cap``
    example paragraphs per candidate word."""
    result = SearchResult(
        examples={word: [] for word in candidates},
        total_hits={word: 0 for word in candidates},
    )
    conn = sqlite3.connect(str(translation_db_path))
    tables = [
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    ]
    for table in tables:
        query = (
            f"SELECT paranum, pali_text, english_translation "
            f'FROM "{table}" WHERE pali_text != ""'
        )
        for paranum, pali_text, english in conn.execute(query):
            result.rows_scanned += 1
            hits = _clean_for_match(pali_text) & candidates
            for word in hits:
                result.total_hits[word] += 1
                bucket = result.examples[word]
                if len(bucket) < cap:
                    bucket.append(
                        Example(
                            source=table,
                            paranum=paranum or "",
                            pali_raw=_strip_html(pali_text),
                            english=(english or "").strip(),
                            word=word,
                        )
                    )
    conn.close()
    return result


# --- translations-table → human book name + canonical (tipiṭaka) order ---

# piṭaka rank by cst filename prefix: vinaya → sutta → abhidhamma → aññā (extra)
_PITAKA_PREFIXES: tuple[tuple[str, int], ...] = (
    ("vin", 0),
    ("abh", 2),
    ("s", 1),
    ("e", 3),
)
# text-layer rank by cst filename extension
_LAYER_RANK: dict[str, int] = {"mul": 0, "att": 1, "tik": 2, "nrf": 3}


def _table_to_cst_filename(table: str) -> str:
    """``e0104n_att`` -> ``e0104n.att``: the translations db uses ``_`` where the
    CST identifier uses ``.``."""
    head, _sep, ext = table.rpartition("_")
    return f"{head}.{ext}" if head else table


def book_label(table: str) -> tuple[str, str]:
    """Return ``(dpd_book_code, human_book_name)`` for a translations-db table,
    falling back to the raw table name when it is unknown."""
    book = from_cst_filename(_table_to_cst_filename(table))
    if book is None:
        return table, table
    code = book.dpd_book_code or book.gui_book_code or book.cst_filename
    return code, book.cst_book_name


def _canonical_sort_key(table: str) -> tuple[int, int, str]:
    """Canonical order: text layer first (mūla→aṭṭhakathā→ṭīkā→aññā), then piṭaka
    within each layer (vinaya→sutta→abhidhamma→aññā)."""
    filename = _table_to_cst_filename(table)
    pitaka = next(
        (rank for prefix, rank in _PITAKA_PREFIXES if filename.startswith(prefix)),
        4,
    )
    layer = _LAYER_RANK.get(filename.rsplit(".", 1)[-1], 4)
    return layer, pitaka, filename


def find_examples_for_word(translation_db_path: Path, word: str) -> list[Example]:
    """Find every translation paragraph containing a word that **starts with**
    ``word`` (prefix / "starts with" match, so a stem like ``disākāka`` matches
    ``disākākaṃ``, ``disākāke`` …).

    Per-word and just-in-time (used by the GUI, which only processes a handful of
    words per session, so the bulk pre-scan above is wasteful there). A SQL
    ``LIKE`` pre-filter — niggahita-flexible via the single-char ``_`` wildcard —
    narrows each table to a few candidate rows, which are then verified in Python
    with a word-start, niggahita-flexible regex (leading boundary only, any
    ending). No cap: all matches are returned, sorted into canonical tipiṭaka
    order. ``Example.source`` carries the DPD book code (e.g. ``VISMa``) and
    ``Example.book_name`` its human name.
    """
    like_pattern = "%" + word.replace("ṃ", "_").replace("ṁ", "_") + "%"
    flexible = re.sub("[ṃṁ]", "[ṃṁ]", re.escape(word))
    verify_re = re.compile(
        rf"(?<![{PALI_LETTERS}])(?:{flexible})",
        re.IGNORECASE,
    )
    collected: list[tuple[tuple[int, int, str], str, Example]] = []
    conn = sqlite3.connect(str(translation_db_path))
    try:
        tables = [
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ]
        for table in tables:
            code, name = book_label(table)
            sort_key = _canonical_sort_key(table)
            query = (
                "SELECT paranum, pali_text, english_translation "
                f'FROM "{table}" WHERE pali_text LIKE ?'
            )
            for paranum, pali_text, english in conn.execute(query, (like_pattern,)):
                stripped = _strip_html(pali_text)
                if verify_re.search(stripped):
                    collected.append(
                        (
                            sort_key,
                            paranum or "",
                            Example(
                                source=code,
                                paranum=paranum or "",
                                pali_raw=stripped,
                                english=(english or "").strip(),
                                word=word,
                                book_name=name,
                            ),
                        )
                    )
    finally:
        conn.close()
    collected.sort(key=lambda item: (item[0], item[1]))
    return [example for _key, _paranum, example in collected]


def _commentary_example(source: CommentarySource, word: str) -> Example:
    """Build example #1 — the commentary the word was pulled from."""
    return Example(
        source=f"commentary: {source.lemma_1}",
        paranum="",
        pali_raw=_strip_html(source.commentary),
        english="",
        word=word,
        is_commentary=True,
    )


def _examples_cell(examples: list[Example]) -> str:
    """Collapse all of a word's examples into a single TSV cell."""
    parts: list[str] = []
    for ex in examples:
        pali = _mark_word(ex.pali_raw, ex.word, "**", "**")[:EXAMPLE_TRUNC]
        english = ex.english[:EXAMPLE_TRUNC] or "—"
        parts.append(f"[{ex.source} {ex.paranum}] {pali} ⇒ {english}")
    return "  ‖  ".join(parts)


# --- display ---


def display_candidate(
    word: str,
    headwords: list[DpdHeadword],
    examples: list[Example],
    total_hits: int,
) -> None:
    pr.green(f"\n■ {word} — {total_hits} paragraph(s)")
    for hw in headwords:
        pr.white(f"    headword: {hw.lemma_1} [{hw.pos}] {hw.meaning_combo}")
    if not examples:
        pr.amber("    no example paragraphs found")
        return
    for i, ex in enumerate(examples, start=1):
        pali = _mark_word(ex.pali_raw, ex.word, ANSI_BOLD, ANSI_RESET)[:EXAMPLE_TRUNC]
        pr.cyan(f"    {i}. ({ex.source} {ex.paranum})")
        pr.white(f"       {pali}")
        pr.white(f"       {ex.english[:EXAMPLE_TRUNC] or '— no english —'}")


def main() -> None:
    pr.tic()
    paths = ProjectPaths()
    gui2_paths = Gui2Paths()
    db_session = get_db_session(paths.dpd_db_path)

    pr.green_title("Pass2x · in commentary — data proof (read-only, simple)")

    exceptions = InCommentaryExceptions(gui2_paths.in_commentary_exceptions_path)

    # step 1
    pr.green_title("Step 1 · collect words from the commentary column")
    pr.bip()
    words, word_source, commentary_rows = harvest_commentary_words(db_session)
    pr.summary("commentary rows used", commentary_rows)
    pr.summary("words harvested", len(words))
    write_tsv(
        [{"word": w} for w in sorted(words)],
        OUTPUT_DIR / "step1_harvested_words.tsv",
    )

    # step 2/3
    pr.green_title("Step 2 · match against inflections of incomplete headwords")
    inflection_map = build_inflection_map(db_session)
    pr.summary("distinct inflections of incomplete headwords", len(inflection_map))

    resolved = {
        w: inflection_map[w]
        for w in words
        if w in inflection_map and w not in exceptions
    }
    pr.summary("excluded by exceptions list", len(exceptions.exceptions))
    pr.summary("commentary words that matched", len(resolved))
    write_tsv(
        [{"word": w, "n_headwords": len(resolved[w])} for w in sorted(resolved)],
        OUTPUT_DIR / "step2_candidates.tsv",
    )
    write_tsv(
        [
            {
                "word": w,
                "id": hw.id,
                "lemma_1": hw.lemma_1,
                "pos": hw.pos,
                "meaning_combo": hw.meaning_combo,
            }
            for w in sorted(resolved)
            for hw in resolved[w]
        ],
        OUTPUT_DIR / "step3_resolved_headwords.tsv",
    )
    pr.summary("step 1-3 time", pr.bop())

    if not resolved:
        pr.red("No commentary words matched — nothing to search.")
        pr.toc()
        return

    # step 4
    pr.green_title("Step 4 · find example paragraphs in the translations db")
    pr.bip()
    search = find_examples_for_candidates(
        paths.tipitaka_translation_db_path, set(resolved.keys())
    )
    pr.summary("translation rows scanned", search.rows_scanned)
    pr.summary("step 4 time", pr.bop())

    # example #1 is always the commentary the word was pulled from,
    # followed by the translation-db paragraphs.
    examples_by_word: dict[str, list[Example]] = {
        w: [_commentary_example(word_source[w], w)] + search.examples[w]
        for w in resolved
    }

    zero_translation = [w for w in resolved if not search.examples[w]]
    pr.summary("matched words with no translation paragraph", len(zero_translation))
    write_tsv(
        [
            {
                "word": w,
                "translation_hits": search.total_hits[w],
                "examples": _examples_cell(examples_by_word[w]),
            }
            for w in sorted(examples_by_word)
        ],
        OUTPUT_DIR / "step4_example_sentences.tsv",
    )

    pr.green_title(f"Sample of {DISPLAY_LIMIT} matched words")
    for word in list(resolved.keys())[:DISPLAY_LIMIT]:
        display_candidate(
            word,
            resolved[word],
            examples_by_word[word],
            search.total_hits[word],
        )

    pr.toc()


if __name__ == "__main__":
    main()
