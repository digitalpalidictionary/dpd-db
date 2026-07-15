"""Tests for tools.cst_source.corpus_index.

Fast tests exercise the row-search semantics on hand-built rows; the slow
test proves byte-identical parity with ``find_cst_source_sutta_example`` on a
real book (including gatha examples).

    uv run pytest tests/tools/cst_source/test_corpus_index.py
    uv run pytest -m slow tests/tools/cst_source/test_corpus_index.py
"""

import pytest

from tools.cst_source import find_cst_source_sutta_example
from tools.cst_source.corpus_index import (
    CstSourceIndex,
    IndexRow,
    _search_book_rows,
)
from tools.cst_source.models import CstSourceSuttaExample


def make_row(
    text: str,
    source: str = "KP 1",
    sutta: str = "saraṇattayaṃ",
    is_gatha: bool = False,
    gatha_examples: list[str] | None = None,
) -> IndexRow:
    return IndexRow(
        source=source,
        sutta=sutta,
        text=text,
        is_gatha=is_gatha,
        gatha_examples=gatha_examples or [],
    )


class TestSearchBookRows:
    def test_sentence_match_includes_neighbours(self) -> None:
        rows = [make_row("Before here. Buddhaṃ saraṇaṃ gacchāmi. After here.")]
        results = _search_book_rows(rows, r"\bsaraṇaṃ\b")
        assert results == [
            CstSourceSuttaExample(
                "KP 1",
                "saraṇattayaṃ",
                "Before here. Buddhaṃ saraṇaṃ gacchāmi. After here.",
            )
        ]

    def test_no_match_returns_nothing(self) -> None:
        rows = [make_row("Dhammaṃ saraṇaṃ gacchāmi.")]
        assert _search_book_rows(rows, r"\bsaṅghaṃ\b") == []

    def test_gatha_row_returns_precomputed_example(self) -> None:
        gatha = "line one, line two, line three."
        rows = [make_row("line two,", is_gatha=True, gatha_examples=[gatha])]
        results = _search_book_rows(rows, r"\btwo\b")
        assert results == [CstSourceSuttaExample("KP 1", "saraṇattayaṃ", gatha)]

    def test_gatha_lines_dedupe_to_one_example(self) -> None:
        gatha = "line one, line two."
        rows = [
            make_row("line one,", is_gatha=True, gatha_examples=[gatha]),
            make_row("line two.", is_gatha=True, gatha_examples=[gatha]),
        ]
        results = _search_book_rows(rows, r"\bline\b")
        assert results == [CstSourceSuttaExample("KP 1", "saraṇattayaṃ", gatha)]

    def test_empty_source_or_sutta_skipped(self) -> None:
        rows = [
            make_row("Buddhaṃ saraṇaṃ.", source=""),
            make_row("Dhammaṃ saraṇaṃ.", sutta=""),
        ]
        assert _search_book_rows(rows, r"\bsaraṇaṃ\b") == []

    def test_order_follows_row_order(self) -> None:
        rows = [
            make_row("First saraṇaṃ here.", sutta="sutta one"),
            make_row("Second saraṇaṃ here.", sutta="sutta two"),
        ]
        results = _search_book_rows(rows, r"\bsaraṇaṃ\b")
        assert [r.sutta for r in results] == ["sutta one", "sutta two"]


@pytest.mark.slow
def test_parity_with_live_extractor_on_kn1() -> None:
    """Index results are byte-identical to the live per-call path for a real
    book, across a match-everything regex (covers gatha and sentence paths)
    and word-level regexes."""
    index = CstSourceIndex(["kn1"])
    for regex in [".", r"\bbuddhaṃ\b", r"\bsaraṇaṃ\b", r"\bhoti\b"]:
        results = index.find_examples(regex)
        assert results, f"no results for {regex} — parity check would be vacuous"
        assert results == find_cst_source_sutta_example("kn1", regex)
