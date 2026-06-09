"""Tests for tools/docs_update_abbreviations.py."""

import json
from pathlib import Path

import pytest

from tools.docs_update_abbreviations import make_abbreviations_md
from tools.paths import ProjectPaths

FIXTURE_PATH = Path(__file__).parent / "test_docs_update_abbreviations_fixtures.json"


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pth() -> ProjectPaths:
    return ProjectPaths()


def test_make_abbreviations_md_golden_master(fixtures, pth):
    """Full output is byte-identical to the frozen fixture."""
    result = make_abbreviations_md(pth)
    assert result == fixtures["make_abbreviations_md"]


def test_make_abbreviations_md_line_count(fixtures, pth):
    """Total line count matches the frozen fixture."""
    result = make_abbreviations_md(pth)
    assert len(result.splitlines()) == fixtures["line_count"]


def test_make_abbreviations_md_grammatical_count(fixtures, pth):
    """Grammatical abbreviation row count matches the frozen fixture."""
    result = make_abbreviations_md(pth)
    lines = result.splitlines()
    textual_start = lines.index("## Textual Abbreviations")
    gram_rows = [
        ln
        for ln in lines[8:textual_start]
        if ln.startswith("|")
        and not ln.startswith("|Abbrev")
        and not ln.startswith("|:")
    ]
    assert len(gram_rows) == fixtures["gram_count"]


def test_make_abbreviations_md_textual_count(fixtures, pth):
    """Textual abbreviation row count matches the frozen fixture."""
    result = make_abbreviations_md(pth)
    lines = result.splitlines()
    textual_start = lines.index("## Textual Abbreviations")
    text_rows = [
        ln
        for ln in lines[textual_start:]
        if ln.startswith("|")
        and not ln.startswith("|Abbrev")
        and not ln.startswith("|:")
    ]
    assert len(text_rows) == fixtures["text_count"]


def test_make_abbreviations_md_structure(pth):
    """Output has the expected section headers and table structure."""
    result = make_abbreviations_md(pth)
    lines = result.splitlines()
    assert lines[0] == "# Abbreviations"
    assert "## Grammatical Abbreviations" in lines
    assert "## Textual Abbreviations" in lines
    assert "|Abbreviation|Meaning|Explanation|" in lines
    assert "|Abbreviation|Meaning|Info|" in lines


def test_make_abbreviations_md_categorisation(pth):
    """Lowercase-start abbreviations go to grammatical; uppercase-start go to textual."""
    result = make_abbreviations_md(pth)
    lines = result.splitlines()
    textual_start = lines.index("## Textual Abbreviations")
    gram_rows = [
        ln
        for ln in lines[8:textual_start]
        if ln.startswith("|")
        and not ln.startswith("|Abbrev")
        and not ln.startswith("|:")
    ]
    text_rows = [
        ln
        for ln in lines[textual_start:]
        if ln.startswith("|")
        and not ln.startswith("|Abbrev")
        and not ln.startswith("|:")
    ]
    # All grammatical abbreviations start with lowercase
    for row in gram_rows:
        abbrev = row.split("|")[1]
        assert not abbrev[0].isupper(), (
            f"Grammatical abbrev starts with uppercase: {abbrev!r}"
        )
    # All textual abbreviations start with uppercase
    for row in text_rows:
        abbrev = row.split("|")[1]
        assert abbrev[0].isupper(), f"Textual abbrev starts with lowercase: {abbrev!r}"
