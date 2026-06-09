"""Golden-master tests for tools/docs_changelog_and_release_notes.py.

Fixtures are captured from real DB data against the current code and frozen in
test_docs_changelog_and_release_notes_fixtures.json. The data-summary methods are
exercised on lightweight stand-ins rebuilt from those fixtures, so a refactor that
silently changes any output string is caught here.
"""

import json
from pathlib import Path
from types import SimpleNamespace

from tools.docs_changelog_and_release_notes import ChangelogGenerator

FIXTURE_PATH = (
    Path(__file__).parent / "test_docs_changelog_and_release_notes_fixtures.json"
)
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _headword_stubs() -> list[SimpleNamespace]:
    stubs = []
    for row in FIXTURES["headwords"]:
        data = dict(row)
        inflections = data.pop("_inflections_list")
        stub = SimpleNamespace(**data)
        stub.inflections_list = inflections
        stubs.append(stub)
    return stubs


def _root_stubs() -> list[SimpleNamespace]:
    return [SimpleNamespace(**row) for row in FIXTURES["roots"]]


def _new_words_stubs() -> list[SimpleNamespace]:
    return [SimpleNamespace(lemma_1=lemma) for lemma in FIXTURES["new_words_lemmas"]]


def _gen() -> ChangelogGenerator:
    return object.__new__(ChangelogGenerator)


def test_format_number() -> None:
    for n, expected in FIXTURES["format_number"].items():
        assert ChangelogGenerator._format_number(int(n)) == expected


def test_get_dpd_size() -> None:
    gen = _gen()
    gen.dpd_db = _headword_stubs()
    gen.root_families = {}
    gen._get_dpd_size()
    assert gen.line_1_headwords == FIXTURES["expected"]["line_1_headwords"]
    assert (
        gen.line_5_cell_of_pali_data == FIXTURES["expected"]["line_5_cell_of_pali_data"]
    )
    assert gen.root_families == FIXTURES["expected"]["root_families"]


def test_get_root_size() -> None:
    gen = _gen()
    gen.roots_db = _root_stubs()
    gen.root_families = FIXTURES["expected"]["root_families"]
    gen._get_root_size()
    assert gen.line_2_roots == FIXTURES["expected"]["line_2_roots"]


def test_get_deconstructor_size() -> None:
    gen = _gen()
    gen.deconstructor_db = [None] * FIXTURES["deconstructor_count"]
    gen._get_deconstructor_size()
    assert gen.line_3_deconstructor == FIXTURES["expected"]["line_3_deconstructor"]


def test_get_inflection_size() -> None:
    gen = _gen()
    gen.dpd_db = _headword_stubs()
    gen._get_inflection_size()
    assert gen.line_4_inflections == FIXTURES["expected"]["line_4_inflections"]


def test_get_root_data() -> None:
    gen = _gen()
    gen.roots_db = _root_stubs()
    gen._get_root_data()
    assert (
        gen.line_6_cells_of_root_data
        == FIXTURES["expected"]["line_6_cells_of_root_data"]
    )


def test_get_new_words() -> None:
    gen = _gen()
    gen.new_words_db = _new_words_stubs()
    gen._get_new_words()
    assert gen.new_words == FIXTURES["expected"]["new_words"]


def test_get_new_words_empty() -> None:
    gen = _gen()
    gen.new_words_db = []
    gen._get_new_words()
    assert gen.new_words == FIXTURES["expected"]["new_words_empty"]
