"""Tests for exporter/pdf/pdf_exporter.py."""

import importlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from exporter.pdf.pdf_exporter import (
    ChunkSpec,
    chunk_source,
    contents_block,
    export_to_pdf,
    extract_section_titles,
    is_entry_snippet,
    split_body_into_chunks,
    update_set_state,
)

FIXTURE_PATH = Path(__file__).parent / "test_pdf_exporter_fixtures.json"


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1. Import-time DB guard: importing the module must NOT open a DB connection
# ---------------------------------------------------------------------------


def test_import_does_not_open_db() -> None:
    """GlobalVars must not run get_db_session at class / import level."""
    call_count = 0

    real_get = None
    import db.db_helpers as _helpers

    real_get = _helpers.get_db_session

    def mock_get_db(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return real_get(*args, **kwargs)

    with patch("db.db_helpers.get_db_session", side_effect=mock_get_db):
        import exporter.pdf.pdf_exporter  # noqa: F401

        importlib.reload(exporter.pdf.pdf_exporter)

    assert call_count == 0, (
        f"get_db_session was called {call_count} time(s) at import — "
        "GlobalVars must not open the DB at class level"
    )


# ---------------------------------------------------------------------------
# 2. Regex fix: [A-Z][A-Za-z] is byte-identical to [A-Z][A-z] on real data
# ---------------------------------------------------------------------------


def test_abbreviation_regex_byte_identical(fixtures: dict) -> None:
    """[A-Z][A-Za-z] must filter exactly the same abbrevs as the old [A-Z][A-z]."""
    rows = fixtures["abbreviations"]
    for row in rows:
        old_result = bool(re.findall(r"[A-Z][A-z]", row["abbrev"]))
        new_result = bool(re.findall(r"[A-Z][A-Za-z]", row["abbrev"]))
        assert new_result == old_result, (
            f"abbrev {row['abbrev']!r}: old={old_result}, new={new_result}"
        )


def test_abbreviation_regex_filtered_count(fixtures: dict) -> None:
    """Exactly 121 of 224 abbrevs are filtered out (book names with double capital)."""
    rows = fixtures["abbreviations"]
    filtered = sum(1 for r in rows if re.findall(r"[A-Z][A-Za-z]", r["abbrev"]))
    assert filtered == 121


# ---------------------------------------------------------------------------
# 3. save_typist_file writes UTF-8 with Pāḷi diacritics intact
# ---------------------------------------------------------------------------


def test_save_typist_file_encoding() -> None:
    """save_typist_file must write UTF-8 so Pāḷi diacritics round-trip correctly."""
    from exporter.pdf.pdf_exporter import save_typist_file

    pali_content = "Namo tassa bhagavato arahato sammāsambuddhassa\n"

    g = MagicMock()
    g.typst_data = [pali_content]

    with tempfile.NamedTemporaryFile(suffix=".typ", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        g.pth.typst_lite_data_path = tmp_path
        save_typist_file(g)
        written = tmp_path.read_text(encoding="utf-8")
        assert written == pali_content
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 4. Chunk splitting
# ---------------------------------------------------------------------------


HEADWORD = "#par[\n  #blue-bold[word]\n]\n"
FAMILY = "\n#heading3[fam]\n#table()\n"
SECTION_HEADER = "#heading(level: 1)[Word Families]\n"
PAGEBREAK = "#pagebreak()\n"
FIRST_LETTER = "#pagebreak()\n#heading(level: 2, outlined: true)[a]\n"


def test_is_entry_snippet() -> None:
    assert is_entry_snippet(HEADWORD)
    assert is_entry_snippet(FAMILY)
    assert not is_entry_snippet(SECTION_HEADER)
    assert not is_entry_snippet(PAGEBREAK)
    assert not is_entry_snippet(FIRST_LETTER)


def test_update_set_state_last_wins() -> None:
    state: dict[str, str] = {}
    update_set_state("#set par(hanging-indent: 1em, spacing: 0.65em)\n", state)
    update_set_state("#set page(columns: 1)\n", state)
    update_set_state("#set par(hanging-indent: 0em, spacing: 0.65em)\n", state)
    assert list(state.values()) == [
        "#set par(hanging-indent: 0em, spacing: 0.65em)",
        "#set page(columns: 1)",
    ]


def test_split_preserves_content_byte_exact() -> None:
    body = [SECTION_HEADER] + [HEADWORD] * 50
    chunks = split_body_into_chunks(body, line_budget=30)
    assert len(chunks) > 1
    rebuilt = "".join("".join(c.body) for c in chunks)
    assert rebuilt == "".join(body)


def test_split_cuts_only_before_entries() -> None:
    body = [SECTION_HEADER] + [HEADWORD] * 50
    chunks = split_body_into_chunks(body, line_budget=30)
    for chunk in chunks[1:]:
        assert is_entry_snippet(chunk.body[0]) or chunk.body[0].startswith(
            ("#pagebreak()", "#heading(level: 1)", "#set ")
        )


def test_split_carries_headers_to_next_chunk() -> None:
    """A section header landing on a cut must open the next chunk, not
    dangle at the end of the previous one."""
    body = (
        [HEADWORD] * 10
        + [PAGEBREAK, SECTION_HEADER, "#set par(hanging-indent: 0em)\n"]
        + [FAMILY] * 10
    )
    line_budget = sum(s.count("\n") for s in body[:12])
    chunks = split_body_into_chunks(body, line_budget=line_budget)
    assert len(chunks) == 2
    assert chunks[0].body == [HEADWORD] * 10
    assert chunks[1].body[0] == PAGEBREAK
    assert chunks[1].body[1] == SECTION_HEADER


def test_split_replays_set_state() -> None:
    body = (
        ["#set page(columns: 1)\n", "#set par(hanging-indent: 1em)\n"]
        + [HEADWORD] * 20
        + ["#set par(hanging-indent: 0em)\n"]
        + [FAMILY] * 20
    )
    chunks = split_body_into_chunks(body, line_budget=30)
    assert len(chunks) >= 2
    assert chunks[0].state_lines == []
    assert "#set page(columns: 1)" in chunks[1].state_lines
    final_par_states = [
        line for line in chunks[-1].state_lines if line.startswith("#set par")
    ]
    assert final_par_states == ["#set par(hanging-indent: 0em)"]


def test_split_single_chunk_when_small() -> None:
    body = [SECTION_HEADER, HEADWORD, HEADWORD]
    chunks = split_body_into_chunks(body, line_budget=100_000)
    assert len(chunks) == 1
    assert chunks[0].body == body
    assert chunks[0].state_lines == []


# ---------------------------------------------------------------------------
# 5. Chunk source assembly
# ---------------------------------------------------------------------------


def test_chunk_source_first_chunk_byte_exact() -> None:
    spec = ChunkSpec(body=[SECTION_HEADER, HEADWORD])
    assert (
        chunk_source("PREAMBLE\n", spec, 1) == "PREAMBLE\n" + SECTION_HEADER + HEADWORD
    )


def test_chunk_source_later_chunk_has_state_and_counter() -> None:
    spec = ChunkSpec(body=[HEADWORD], state_lines=["#set page(columns: 1)"])
    source = chunk_source("PREAMBLE\n", spec, 998)
    assert "#set page(columns: 1)" in source
    assert "#counter(page).update(998)" in source
    assert source.index("#counter(page).update(998)") < source.index(HEADWORD)


def test_chunk_source_strips_leading_pagebreak() -> None:
    """A carried header's pagebreak is redundant at chunk start and
    would insert a blank page."""
    spec = ChunkSpec(body=[FIRST_LETTER, HEADWORD], state_lines=[])
    source = chunk_source("PREAMBLE\n", spec, 500)
    assert "#pagebreak()" not in source
    assert "#heading(level: 2, outlined: true)[a]" in source


# ---------------------------------------------------------------------------
# 6. Section titles and contents page
# ---------------------------------------------------------------------------


def test_extract_section_titles() -> None:
    snippets = [
        "#hide[\n  #heading(level: 1)[Title Page]\n]\n",
        SECTION_HEADER,
        FIRST_LETTER,  # level 2: excluded
        HEADWORD,
    ]
    assert extract_section_titles(snippets) == ["Title Page", "Word Families"]


def test_contents_block() -> None:
    block = contents_block([("Abbreviations", 5), ("Pāḷi to English Dictionary", 8)])
    assert "Abbreviations #box(width: 1fr, repeat[.]) 5 \\\n" in block
    assert "Pāḷi to English Dictionary #box(width: 1fr, repeat[.]) 8 \\\n" in block


# ---------------------------------------------------------------------------
# 7. End-to-end: split, compile, contents, merge (requires typst CLI)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(shutil.which("typst") is None, reason="typst CLI not on PATH")
def test_export_to_pdf_end_to_end(tmp_path: Path) -> None:
    """Real chunked pipeline on a tiny synthetic document: continuous
    page numbers, rebuilt contents page, nested bookmarks, cleanup."""
    from pypdf import PdfReader

    preamble = '#set page(paper: "a5", numbering: "1")\n'
    front = "#hide[\n  #heading(level: 1)[Front]\n]\n#outline(depth: 1)\n"
    body = [
        front,
        PAGEBREAK,
        "#heading(level: 1)[Words]\n",
        "#par[entry one]\n",
        "#par[entry two]\n",
        "#par[entry three]\n",
    ]

    g = MagicMock()
    g.typst_data = [preamble, *body]
    g.pth.typst_lite_data_path = tmp_path / "typst_data_lite.typ"
    g.pth.typst_lite_pdf_path = tmp_path / "dpd.pdf"

    with patch("exporter.pdf.pdf_exporter.CHUNK_LINE_BUDGET", 1):
        export_to_pdf(g)

    merged = PdfReader(g.pth.typst_lite_pdf_path)
    n_pages = len(merged.pages)
    assert n_pages >= 2

    # printed page numbers are continuous and match physical position
    for index in range(n_pages):
        text = merged.pages[index].extract_text() or ""
        assert str(index + 1) in text

    # contents page lists the body section with its real page number
    front_text = merged.pages[0].extract_text() or ""
    assert "Words" in front_text

    # bookmarks: both sections present at top level
    top_titles = [
        item["/Title"] for item in merged.outline if not isinstance(item, list)
    ]
    assert top_titles == ["Front", "Words"]

    # chunk working files are cleaned up
    assert not list(tmp_path.glob("typst_chunk_*"))
