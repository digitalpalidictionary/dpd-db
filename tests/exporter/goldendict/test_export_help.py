"""Golden-master tests for exporter/goldendict/export_help.py."""

import json
from pathlib import Path

import pytest

from exporter.goldendict.data_classes import AbbreviationsData
from exporter.goldendict.export_help import (
    Abbreviation,
    Help,
    add_abbrev_html,
    add_abbrev_other_html,
    add_bibliography,
    add_help_html,
    add_thanks,
)
from exporter.jinja2_env import get_jinja2_env
from tools.paths import ProjectPaths

FIXTURE_PATH = Path(__file__).parent / "test_export_help_fixtures.json"


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pth() -> ProjectPaths:
    return ProjectPaths()


@pytest.fixture(scope="module")
def jinja_env():
    return get_jinja2_env("exporter/goldendict/templates")


@pytest.fixture(scope="module")
def header(jinja_env):
    return AbbreviationsData(None, jinja_env).header


# --- Abbreviation / Help dataclass attribute access ---


def test_abbreviation_attrs(fixtures: dict) -> None:
    obj = Abbreviation(
        abbrev="abbrev_val",
        meaning="meaning_val",
        pali="pali_val",
        example="ex",
        information="info",
    )
    f = fixtures["abbreviation_attrs"]
    assert obj.abbrev == f["abbrev"]
    assert obj.meaning == f["meaning"]
    assert obj.pali == f["pali"]
    assert obj.example == f["example"]
    assert obj.information == f["information"]


def test_help_attrs(fixtures: dict) -> None:
    obj = Help(help="help_val", meaning="meaning_val2")
    f = fixtures["help_attrs"]
    assert obj.help == f["help"]
    assert obj.meaning == f["meaning"]


# --- DictEntry counts match frozen baseline ---


def test_abbrev_count(pth: ProjectPaths, jinja_env, fixtures: dict) -> None:
    entries = add_abbrev_html(pth, jinja_env)
    assert len(entries) == fixtures["abbrev_count"]


def test_abbrev_other_count(pth: ProjectPaths, jinja_env, fixtures: dict) -> None:
    entries = add_abbrev_other_html(pth, jinja_env)
    assert len(entries) == fixtures["abbrev_other_count"]


def test_help_count(pth: ProjectPaths, jinja_env, fixtures: dict) -> None:
    entries = add_help_html(pth, jinja_env)
    assert len(entries) == fixtures["help_count"]


# --- First-3 DictEntry content frozen (word + definition_html) ---


@pytest.mark.parametrize("idx", [0, 1, 2])
def test_abbrev_sample(pth: ProjectPaths, jinja_env, fixtures: dict, idx: int) -> None:
    entries = add_abbrev_html(pth, jinja_env)
    expected = fixtures["abbrev_sample"][idx]
    assert entries[idx].word == expected["word"]
    assert entries[idx].definition_html == expected["definition_html"]


@pytest.mark.parametrize("idx", [0, 1, 2])
def test_abbrev_other_sample(
    pth: ProjectPaths, jinja_env, fixtures: dict, idx: int
) -> None:
    entries = add_abbrev_other_html(pth, jinja_env)
    expected = fixtures["abbrev_other_sample"][idx]
    assert entries[idx].word == expected["word"]
    assert entries[idx].definition_html == expected["definition_html"]


@pytest.mark.parametrize("idx", [0, 1, 2])
def test_help_sample(pth: ProjectPaths, jinja_env, fixtures: dict, idx: int) -> None:
    entries = add_help_html(pth, jinja_env)
    expected = fixtures["help_sample"][idx]
    assert entries[idx].word == expected["word"]
    assert entries[idx].definition_html == expected["definition_html"]


# --- bibliography / thanks: word, synonyms and full HTML frozen (covers zip loop) ---


def test_bibliography(pth: ProjectPaths, header: str, fixtures: dict) -> None:
    entries = add_bibliography(pth, header)
    f = fixtures["bibliography"]
    assert entries[0].word == f["word"]
    assert entries[0].synonyms == f["synonyms"]
    assert entries[0].definition_html == f["definition_html"]


def test_thanks(pth: ProjectPaths, header: str, fixtures: dict) -> None:
    entries = add_thanks(pth, header)
    f = fixtures["thanks"]
    assert entries[0].word == f["word"]
    assert entries[0].synonyms == f["synonyms"]
    assert entries[0].definition_html == f["definition_html"]
