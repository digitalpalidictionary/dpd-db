"""Golden-master tests for _make_synonyms in deconstructor_exporter."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from exporter.deconstructor.deconstructor_exporter import _make_synonyms

FIXTURE_PATH = Path(__file__).parent / "test_deconstructor_exporter_fixtures.json"
FIXTURES: dict = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case_key", FIXTURES.keys())
def test_make_synonyms_matches_fixture(case_key: str) -> None:
    case = FIXTURES[case_key]
    lookup_key = case["lookup_key"]

    i = SimpleNamespace(
        lookup_key=lookup_key,
        sinhala_unpack=case["sinhala_unpack"],
        devanagari_unpack=case["devanagari_unpack"],
        thai_unpack=case["thai_unpack"],
    )
    speech_marks = (
        {lookup_key: case["speech_marks_entry"]} if case["speech_marks_entry"] else {}
    )

    result = _make_synonyms(i, speech_marks)

    assert result == case["expected_synonyms"]


def test_make_synonyms_no_speech_marks_key_returns_no_extra() -> None:
    """A key absent from speech_marks produces no extra synonyms."""
    i = SimpleNamespace(
        lookup_key="testword",
        sinhala_unpack=[],
        devanagari_unpack=[],
        thai_unpack=[],
    )
    result = _make_synonyms(i, {})
    assert result == ["testword"]
