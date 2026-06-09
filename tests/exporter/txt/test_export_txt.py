"""Golden-master tests for exporter/txt/export_txt.make_word_entry."""

import json
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from exporter.txt.export_txt import make_word_entry
from tools.paths import ProjectPaths

FIXTURE_PATH = Path(__file__).parent / "test_export_txt_fixtures.json"


def load_fixtures() -> dict[str, dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def get_headword(hw_id: int) -> DpdHeadword:
    pth = ProjectPaths()
    db = get_db_session(pth.dpd_db_path)
    return db.query(DpdHeadword).filter(DpdHeadword.id == hw_id).one()


class TestMakeWordEntry:
    """make_word_entry output is byte-identical to the golden master."""

    def _run(self, hw_id: int) -> tuple[str, str]:
        fixtures = load_fixtures()
        expected = fixtures[str(hw_id)]["output"]
        hw = get_headword(hw_id)
        actual = make_word_entry(hw)
        return expected, actual

    def test_branch1_with_root_and_extras_id8(self):
        expected, actual = self._run(8)
        assert actual == expected

    def test_branch1_with_root_and_extras_id9(self):
        expected, actual = self._run(9)
        assert actual == expected

    def test_branch1_with_root_and_extras_id10(self):
        expected, actual = self._run(10)
        assert actual == expected

    def test_branch2_pass1_or_pass2_id967(self):
        expected, actual = self._run(967)
        assert actual == expected

    def test_branch2_pass1_or_pass2_id1521(self):
        expected, actual = self._run(1521)
        assert actual == expected

    def test_branch3_no_meaning_no_pass_id15(self):
        expected, actual = self._run(15)
        assert actual == expected

    def test_branch3_no_meaning_no_pass_id21(self):
        expected, actual = self._run(21)
        assert actual == expected

    def test_branch1_trad_lemma_diff_id394(self):
        expected, actual = self._run(394)
        assert actual == expected
