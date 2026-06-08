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


def test_convert_newlines_headword() -> None:
    hw = SimpleNamespace(
        construction="a\nb",
        phonetic="p",
        notes="x\ny\nz",
        commentary="",
        example_1=123,
        missing_skipped=None,
    )
    dc.HeadwordData._convert_newlines(hw)
    expected = FIXTURES["convert_newlines_headword"]
    assert hw.construction == expected["construction"]
    assert hw.phonetic == expected["phonetic"]
    assert hw.notes == expected["notes"]
    assert hw.commentary == expected["commentary"]
    assert hw.example_1 == expected["example_1"]


def test_convert_newlines_roots() -> None:
    rt = SimpleNamespace(
        panini_root="r1\nr2",
        panini_sanskrit="",
        panini_english="e\nf",
    )
    dc.RootsData._convert_newlines(rt)
    expected = FIXTURES["convert_newlines_roots"]
    assert rt.panini_root == expected["panini_root"]
    assert rt.panini_sanskrit == expected["panini_sanskrit"]
    assert rt.panini_english == expected["panini_english"]


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
