"""Golden-master tests for db/lookup/spelling_mistakes.py::load_spelling_dict."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from db.lookup.spelling_mistakes import load_spelling_dict

FIXTURE_PATH = Path(__file__).parent / "test_spelling_mistakes_fixtures.json"
TSV_PATH = Path("shared_data/deconstructor/spelling_mistakes.tsv")


@pytest.fixture
def fixture_data() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def make_g(tsv_path: Path = TSV_PATH) -> SimpleNamespace:
    pth = SimpleNamespace(spelling_mistakes_path=tsv_path)
    return SimpleNamespace(pth=pth, spellings_dict=None)


def test_total_count(fixture_data: dict) -> None:
    g = make_g()
    load_spelling_dict(g)
    assert len(g.spellings_dict) == fixture_data["total_count"]


def test_sample_entries(fixture_data: dict) -> None:
    g = make_g()
    load_spelling_dict(g)
    for mistake, corrections in fixture_data["sample"].items():
        assert mistake in g.spellings_dict
        assert sorted(g.spellings_dict[mistake]) == corrections


def test_header_row_skipped(fixture_data: dict) -> None:
    g = make_g()
    load_spelling_dict(g)
    assert "mistake" not in g.spellings_dict
    assert "correction" not in g.spellings_dict


def test_values_are_sets() -> None:
    g = make_g()
    load_spelling_dict(g)
    for v in g.spellings_dict.values():
        assert isinstance(v, set)
