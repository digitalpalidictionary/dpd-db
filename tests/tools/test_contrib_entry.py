from pathlib import Path
from types import SimpleNamespace
from typing import cast

from db.models import DpdHeadword
from gui2.additions_manager import AdditionsManager
from gui2.paths import Gui2Paths
from gui2.toolkit import ToolKit
from tools.contrib_entry import delivered_files, entry_hash


def _manager(tmp_path: Path, username: str) -> AdditionsManager:
    paths = Gui2Paths.for_user(username, base_dir=tmp_path)
    paths.gui2_data_path.mkdir(parents=True, exist_ok=True)
    return AdditionsManager(cast(ToolKit, SimpleNamespace(paths=paths)))


def test_hash_ignores_key_order() -> None:
    assert entry_hash({"a": 1, "b": "ā"}) == entry_hash({"b": "ā", "a": 1})


def test_hash_changes_with_a_value() -> None:
    assert entry_hash({"meaning_1": "horse"}) != entry_hash({"meaning_1": "mare"})


def test_hash_survives_the_contributor_file_round_trip(tmp_path: Path) -> None:
    word = DpdHeadword()
    word.id = 10_000_001
    word.lemma_1 = "ṭīkā 1"
    word.meaning_1 = "sub-commentary"
    alice = _manager(tmp_path, "alice")
    alice.add_additions(word, "a note")
    written = alice.additions_dict["alice_10000001"]

    # The maintainer's loader reads the same file back from disk.
    loaded = _manager(tmp_path, "1").additions_dict["alice_10000001"]

    assert entry_hash(loaded) == entry_hash(written)


def test_delivered_files_skip_review_logs_and_session_files(tmp_path: Path) -> None:
    names = [
        "additions_alice.json",
        "additions_added_alice.json",
        "corrections_alice.json",
        "corrections_added_alice.json",
        "history_alice.json",
        "daily_log_alice.json",
        "headword_stash_alice.json",
        "filter_presets_alice.json",
        "user_dictionary_alice.txt",
        "db_test_exceptions_alice.tsv",
    ]
    for name in names:
        (tmp_path / name).write_text("")

    found = delivered_files(tmp_path)

    assert [p.name for p in found["additions"]] == ["additions_alice.json"]
    assert [p.name for p in found["corrections"]] == ["corrections_alice.json"]
    assert [p.name for p in found["user_dictionary"]] == ["user_dictionary_alice.txt"]
    assert [p.name for p in found["db_test_exceptions"]] == [
        "db_test_exceptions_alice.tsv"
    ]
    delivered = {p.name for paths in found.values() for p in paths}
    assert delivered == {
        "additions_alice.json",
        "corrections_alice.json",
        "user_dictionary_alice.txt",
        "db_test_exceptions_alice.tsv",
    }
