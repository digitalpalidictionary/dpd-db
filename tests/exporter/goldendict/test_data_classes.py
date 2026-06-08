"""Characterization tests for exporter/goldendict/data_classes.py.

Freezes the output of the pure transforms and the per-entry HTML header
rendering so the type-hint + header-dedup refactor stays byte-identical.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from exporter.goldendict import data_classes as dc
from exporter.jinja2_env import get_jinja2_env

FIXTURE_PATH = Path(__file__).parent / "test_data_classes_fixtures.json"
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_newline_view_matches_frozen_conversion() -> None:
    """The view reproduces the original _convert_newlines output byte-for-byte
    for the display fields, WITHOUT mutating the underlying object."""
    hw = SimpleNamespace(
        construction="a\nb",
        phonetic="p",
        notes="x\ny\nz",
        commentary="",
        example_1=123,
        missing_skipped=None,
    )
    view = dc._NewlineView(hw)  # type: ignore[arg-type]
    expected = FIXTURES["convert_newlines_headword"]
    assert view.construction == expected["construction"]
    assert view.phonetic == expected["phonetic"]
    assert view.notes == expected["notes"]
    assert view.commentary == expected["commentary"]
    assert view.example_1 == expected["example_1"]
    # the source ORM object must be untouched
    assert hw.construction == "a\nb"
    assert hw.notes == "x\ny\nz"


def test_newline_view_delegates_non_display_attrs() -> None:
    hw = SimpleNamespace(lemma_1="gacchati", compound_type="kammadhāraya", pos="vb")
    view = dc._NewlineView(hw)  # type: ignore[arg-type]
    assert view.lemma_1 == "gacchati"
    assert view.compound_type == "kammadhāraya"
    assert view.pos == "vb"


def test_convert_newlines_removed() -> None:
    """Regression guard: the ORM-mutating helpers must not return."""
    assert not hasattr(dc.HeadwordData, "_convert_newlines")
    assert not hasattr(dc.RootsData, "_convert_newlines")


def test_epd_generate_html_string() -> None:
    entry = object.__new__(dc.EpdData)
    entry.epd_entries = [("gacchati", "vb", "goes (acc)"), ("dhamma", "nt", "nature")]
    assert entry._generate_html_string() == FIXTURES["epd_html_string"]


def test_epd_generate_html_string_empty() -> None:
    entry = object.__new__(dc.EpdData)
    entry.epd_entries = []
    assert entry._generate_html_string() == FIXTURES["epd_html_string_empty"]


PLAIN_HEADER_CLASSES = [
    "EpdData",
    "VariantData",
    "SeeData",
    "SpellingData",
    "AbbreviationsData",
    "AbbrevOtherData",
    "HelpData",
]


@pytest.mark.parametrize("cls_name", PLAIN_HEADER_CLASSES)
def test_plain_header_rendering(cls_name: str) -> None:
    env = get_jinja2_env("exporter/goldendict/templates")
    obj = object.__new__(getattr(dc, cls_name))
    obj.jinja_env = env
    assert obj._generate_header() == FIXTURES[f"header_{cls_name}"]
