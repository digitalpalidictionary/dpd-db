"""Tests for the kindle exporter's KindleData: it must never mutate the
source DpdHeadword, computing html-friendly text into a separate dict
instead, while summary/grammar rendering still behaves as before."""

from types import SimpleNamespace
from typing import cast

from jinja2 import Environment

from db.models import DpdHeadword
from exporter.jinja2_env import get_jinja2_env
from exporter.kindle.data_classes import KindleData, _make_friendly, html_friendly


def _env() -> Environment:
    return get_jinja2_env("exporter/kindle/templates")


def _headword(**overrides) -> DpdHeadword:
    base = dict(
        pos="masc",
        plus_case="",
        meaning_combo_html="",
        construction_summary="",
        degree_of_completion_html="",
        meaning_1="",
        grammar="",
        neg="",
        verb="",
        trans="",
        root_base="",
        construction="",
        sanskrit="",
        compound_type="",
        phonetic="",
        example_1="",
        example_2="",
        sutta_1="",
        sutta_2="",
        commentary="",
        notes="",
        cognate="",
        lemma_ipa="dəmmə",
        family_root="",
        root_key="",
        derivative="",
        antonym="",
        synonym="",
        variant="",
        link="",
        non_ia="",
        source_1="",
        source_2="",
    )
    base.update(overrides)
    return cast(DpdHeadword, SimpleNamespace(**base))


def test_html_friendly_converts_newlines_and_angle_brackets() -> None:
    assert html_friendly("a\nb") == "a<br/>b"
    assert html_friendly("a > b") == "a &gt; b"
    assert html_friendly("a < b") == "a &lt; b"


def test_make_friendly_returns_html_friendly_values_without_mutating_source() -> None:
    headword = _headword(example_1="line1\nline2")
    friendly = _make_friendly(headword)

    assert friendly["example_1"] == "line1<br/>line2"
    assert headword.example_1 == "line1\nline2"


def test_make_friendly_only_includes_the_twelve_friendly_attrs() -> None:
    headword = _headword(lemma_ipa="dəmmə")
    friendly = _make_friendly(headword)

    assert "lemma_ipa" not in friendly


def test_make_friendly_skips_non_string_attrs() -> None:
    headword = _headword(commentary=None)
    friendly = _make_friendly(headword)

    assert "commentary" not in friendly


def test_kindle_data_has_no_pth_attribute() -> None:
    data = KindleData(_headword(), _env(), 1, [])
    assert not hasattr(data, "pth")


def test_kindle_data_skips_friendly_computation_without_meaning_1() -> None:
    data = KindleData(_headword(meaning_1=""), _env(), 1, [])
    assert data.friendly == {}


def test_kindle_data_summary_escapes_ampersand() -> None:
    headword = _headword(meaning_combo_html="this & that")
    data = KindleData(headword, _env(), 1, [])
    assert "&amp;" in data.summary
    assert " & " not in data.summary


def test_kindle_data_does_not_mutate_source_headword() -> None:
    headword = _headword(
        meaning_1="dhamma things",
        example_1="ex1\nline2",
        commentary="note\nmore",
    )
    KindleData(headword, _env(), 1, [])
    assert headword.example_1 == "ex1\nline2"
    assert headword.commentary == "note\nmore"


def test_kindle_data_examples_are_html_friendly_in_render() -> None:
    headword = _headword(meaning_1="dhamma things", example_1="ex1\nline2")
    data = KindleData(headword, _env(), 1, [])
    assert "ex1<br/>line2" in data.examples
