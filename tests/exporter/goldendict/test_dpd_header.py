# -*- coding: utf-8 -*-
"""Tests for dpd_header.jinja — frequency block guard.

Fixtures are real ``dpd_headwords`` rows captured into
``test_dpd_header_fixtures.json``, including the rendered header HTML as a
golden master. ``cf_set`` / ``idioms_set`` membership is frozen from the
capture so the tests do not depend on live cache files.
"""

# ruff: noqa: E402

import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

sys.modules.setdefault(
    "aksharamukha",
    types.SimpleNamespace(
        transliterate=types.SimpleNamespace(process=lambda *args, **kwargs: "")
    ),
)

from db.models import DpdHeadword
from exporter.jinja2_env import get_jinja2_env

FIXTURES = json.loads(
    (Path(__file__).parent / "test_dpd_header_fixtures.json").read_text(
        encoding="utf-8"
    )
)


def _make_headword(fixture: dict) -> DpdHeadword:
    hw = DpdHeadword(**fixture["columns"])
    hw.cf_set = frozenset(fixture["cf_set_members"])
    hw.idioms_set = frozenset(fixture["idioms_set_members"])
    return hw


def _render(fixture: dict) -> str:
    env = get_jinja2_env("exporter/goldendict/templates")
    template = env.get_template("dpd_header.jinja")
    d = SimpleNamespace(i=_make_headword(fixture), date=FIXTURES["fixed_date"])
    return template.render(d=d)


class TestGoldenMaster:
    def test_root_compound_set_word_byte_identical(self):
        fixture = FIXTURES["golden_root_compound_set"]
        assert _render(fixture) == fixture["header_html"]

    def test_word_family_word_byte_identical(self):
        fixture = FIXTURES["golden_word_family"]
        assert _render(fixture) == fixture["header_html"]


class TestEmptyFreqData:
    """A freq-eligible pos with empty freq_data (a word added after the last
    frequency run) used to crash the render with
    ``TypeError: Object of type Undefined is not JSON serializable``.
    The guard now omits the frequency keys instead."""

    def test_renders_without_crash_and_omits_freq_keys(self):
        fixture = FIXTURES["empty_freq_data"]
        assert fixture["columns"]["freq_data"] == ""
        hw = _make_headword(fixture)
        assert hw.needs_frequency_button

        html = _render(fixture)
        assert "CstFreq" not in html
        assert "FreqHeading" not in html
        assert f'"id": {fixture["columns"]["id"]}' in html
