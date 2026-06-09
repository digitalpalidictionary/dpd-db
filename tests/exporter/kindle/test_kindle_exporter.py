"""Golden-master tests for exporter/kindle/kindle_exporter.py.

Real-data characterization tests (no mocks). The fixture JSON freezes the
output of the render functions as produced by the pre-refactor code; these
tests assert the refactored functions reproduce it byte-for-byte.

The deconstructor-selection fix (deleting the buggy
``set(i.lookup_key) & all_words_set`` filter) is a deliberate behaviour change:
the EBT word pre-filter already limits ``deconstructor_db`` to sutta-corpus
compounds, so the extra char-intersection only dropped 19 legitimate EBT
compounds. Those keys are frozen in ``dropped_19`` and asserted to be real
deconstructor rows that render correctly; every other output stays identical.
"""

import json
from pathlib import Path

import pytest

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from exporter.jinja2_env import get_jinja2_env
from tools.paths import ProjectPaths

import exporter.kindle.kindle_exporter as ke

FIXTURE_PATH = Path(__file__).parent / "test_kindle_exporter_fixtures.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pth() -> ProjectPaths:
    return ProjectPaths()


@pytest.fixture(scope="module")
def jinja_env():
    return get_jinja2_env("exporter/kindle/templates")


@pytest.fixture(scope="module")
def db(pth: ProjectPaths):
    session = get_db_session(pth.dpd_db_path)
    session.autoflush = False
    yield session
    session.close()


@pytest.mark.parametrize("case", FIXTURE["html_friendly"])
def test_html_friendly_matches_frozen(case: dict) -> None:
    assert ke.html_friendly(case["input"]) == case["output"]


@pytest.mark.parametrize("case", FIXTURE["render_deconstructor_entry"])
def test_render_deconstructor_entry_matches_frozen(case: dict, jinja_env, db) -> None:
    row = db.query(Lookup).filter(Lookup.lookup_key == case["lookup_key"]).first()
    assert row is not None
    result = ke.render_deconstructor_entry(
        jinja_env, case["counter"], row, case["script_inflections"]
    )
    assert result == case["output"]


@pytest.mark.parametrize("case", FIXTURE["render_ebook_letter_templ"])
def test_render_ebook_letter_templ_matches_frozen(case: dict, jinja_env) -> None:
    result = ke.render_ebook_letter_templ(jinja_env, case["letter"], case["entries"])
    assert result == case["output"]


@pytest.mark.parametrize("case", FIXTURE["render_abbreviation_entry"])
def test_render_abbreviation_entry_matches_frozen(case: dict, jinja_env) -> None:
    result = ke.render_abbreviation_entry(jinja_env, case["counter"], case["i"])
    assert result == case["output"]


@pytest.mark.parametrize("case", FIXTURE["render_epd_entry"])
def test_render_epd_entry_matches_frozen(case: dict, jinja_env) -> None:
    result = ke.render_epd_entry(
        jinja_env,
        case["counter"],
        case["english_headword"],
        case["pali_equivalents"],
    )
    assert result == case["output"]


@pytest.mark.parametrize("case", FIXTURE["render_epd_letter_templ"])
def test_render_epd_letter_templ_matches_frozen(case: dict, jinja_env) -> None:
    result = ke.render_epd_letter_templ(jinja_env, case["letter"], case["entries"])
    assert result == case["output"]


@pytest.mark.parametrize("case", FIXTURE["render_ebook_entry"])
def test_render_ebook_entry_matches_frozen(
    case: dict, pth: ProjectPaths, jinja_env, db
) -> None:
    hw = db.query(DpdHeadword).filter(DpdHeadword.id == case["id"]).first()
    assert hw is not None
    result = ke.render_ebook_entry(
        pth,
        jinja_env,
        case["counter"],
        hw,
        case["inflections"],
        case["script_inflections"],
    )
    assert result == case["output"]


def test_dropped_19_are_real_ebt_deconstructor_rows(db) -> None:
    """The 19 EBT compounds the old char-intersection filter wrongly dropped.

    Each is a genuine deconstructor row, so deleting the filter correctly adds
    them to the ebook (behaviour change, +19 of 20,298 deconstructor entries).
    """
    dropped = FIXTURE["dropped_19"]
    assert len(dropped) == 19
    for key in dropped:
        row = db.query(Lookup).filter(Lookup.lookup_key == key).first()
        assert row is not None, key
        assert row.deconstructor != "", key
