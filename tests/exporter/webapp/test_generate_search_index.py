import json
from pathlib import Path

import pytest

from exporter.webapp.generate_search_index import build_index, strip_diacritics

FIXTURE_PATH = Path(__file__).parent / "test_generate_search_index_fixtures.json"
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_strip_diacritics():
    assert strip_diacritics("bhū") == "bhu"
    assert strip_diacritics("√bhū") == "bhu"
    assert strip_diacritics("rūpa") == "rupa"
    assert strip_diacritics("ñāṇa") == "nana"
    assert strip_diacritics("Pāḷi") == "Pali"


def test_build_index():
    terms = {"bhū", "bhu", "rūpa", "rupa"}
    expected = ["bhu|bhu|bhū", "rupa|rupa|rūpa"]
    assert build_index(terms) == expected


def test_build_index_sorting():
    # Test alphabetical order of primary keys
    terms = {"rūpa", "bhū", "bhu"}
    index = build_index(terms)
    assert index[0] == "bhu|bhu|bhū"
    assert index[1] == "rupa|rūpa"


@pytest.mark.parametrize("text", list(FIXTURES["strip_diacritics"].keys()))
def test_strip_diacritics_golden(text: str) -> None:
    assert strip_diacritics(text) == FIXTURES["strip_diacritics"][text]


@pytest.mark.parametrize("name", list(FIXTURES["build_index"].keys()))
def test_build_index_golden(name: str) -> None:
    case = FIXTURES["build_index"][name]
    assert build_index(set(case["input"])) == case["output"]
