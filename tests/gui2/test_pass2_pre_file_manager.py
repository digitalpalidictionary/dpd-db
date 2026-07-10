from pathlib import Path

from gui2.books import SuttaCentralSegment
from gui2.pass2_pre_file_manager import Pass2PreFileManager
from gui2.paths import Gui2Paths


def _manager(tmp_path: Path, book: str = "dn") -> Pass2PreFileManager:
    paths = Gui2Paths(base_dir=tmp_path)
    return Pass2PreFileManager(book, paths)


class TestLoadData:
    def test_missing_file_starts_empty(self, tmp_path: Path):
        pfm = _manager(tmp_path)
        assert pfm.unmatched == {}
        assert pfm.matched == {}
        assert pfm.new_word == {}
        assert pfm.processed == []


class TestUpdateUnmatched:
    def test_adds_new_entry(self, tmp_path: Path):
        pfm = _manager(tmp_path)
        msg = pfm.update_unmatched("word1", 5)
        assert "word1" in msg
        assert pfm.unmatched == {"word1": [5]}

    def test_does_not_duplicate_same_id(self, tmp_path: Path):
        pfm = _manager(tmp_path)
        pfm.update_unmatched("word1", 5)
        pfm.update_unmatched("word1", 5)
        assert pfm.unmatched == {"word1": [5]}

    def test_persists_across_reload(self, tmp_path: Path):
        pfm = _manager(tmp_path)
        pfm.update_unmatched("word1", 5)
        reloaded = _manager(tmp_path)
        assert reloaded.unmatched == {"word1": [5]}


class TestUpdateMatched:
    def test_adds_entry(self, tmp_path: Path):
        pfm = _manager(tmp_path)
        sentence = SuttaCentralSegment(segment="dn1:1.1", pali="x", english="y")
        pfm.update_matched("word2", 6, sentence)
        assert pfm.matched == {"word2": {"id": 6, "sentence": sentence}}


class TestMoveMatchedItemToProcessed:
    def test_moves_existing_item(self, tmp_path: Path):
        pfm = _manager(tmp_path)
        pfm.update_matched(
            "word2", 6, SuttaCentralSegment(segment="dn1:1.1", pali="x", english="y")
        )
        msg = pfm.move_matched_item_to_processed("word2")
        assert "word2" in msg
        assert pfm.matched == {}
        assert pfm.processed == ["word2"]

    def test_missing_item_reports_not_found(self, tmp_path: Path):
        pfm = _manager(tmp_path)
        msg = pfm.move_matched_item_to_processed("not_present")
        assert "not found" in msg


class TestGetNextNewWord:
    def test_returns_none_when_empty(self, tmp_path: Path):
        pfm = _manager(tmp_path)
        assert pfm.get_next_new_word() == (None, None)

    def test_pops_next_item(self, tmp_path: Path):
        pfm = _manager(tmp_path)
        sentence_data = SuttaCentralSegment(segment="dn1:1.1", pali="z", english="w")
        pfm.update_new_word("word3", sentence_data)
        word, sentence = pfm.get_next_new_word()
        assert word == "word3"
        assert sentence == sentence_data
        assert pfm.new_word == {}
