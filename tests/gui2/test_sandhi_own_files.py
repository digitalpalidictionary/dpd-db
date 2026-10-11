"""The Pass1Add sandhi buttons write the per-user files for a contributor and
the shared files for user 1."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from gui2.database_manager import DatabaseManager
from gui2.mixins import SandhiOK
from gui2.paths import Gui2Paths
from gui2.sandhi_files_manager import SandhiFileManager


def make_paths(tmp_path: Path, username: str) -> Gui2Paths:
    paths = Gui2Paths.for_user(username, base_dir=tmp_path)
    paths.gui2_data_path.mkdir(parents=True, exist_ok=True)
    paths.sandhi_checked_path.parent.mkdir(parents=True, exist_ok=True)
    return paths


class Host(SandhiOK):
    def __init__(self, paths: Gui2Paths) -> None:
        self.gui2pth = paths


def test_mixin_contributor_writes_own_files_only(tmp_path: Path) -> None:
    alice = make_paths(tmp_path, "alice")
    shared = make_paths(tmp_path, "1")

    Host(alice).update_sandhi_corrections("aniccomhi", "anicco + amhi")
    Host(alice).update_sandhi_checked("ekova")

    assert alice.sandhi_corrections_path.read_text(encoding="utf-8") == (
        "aniccomhi\tanicco + amhi\n"
    )
    assert alice.sandhi_checked_path.read_text(encoding="utf-8") == (
        "aniccomhi\nekova\n"
    )
    assert not shared.sandhi_corrections_path.exists()
    assert not shared.sandhi_checked_path.exists()


def test_mixin_user_one_writes_shared_files(tmp_path: Path) -> None:
    shared = make_paths(tmp_path, "1")

    Host(shared).update_sandhi_corrections("aniccomhi", "anicco + amhi")

    assert shared.sandhi_corrections_path.read_text(encoding="utf-8") == (
        "aniccomhi\tanicco + amhi\n"
    )
    assert shared.sandhi_checked_path.read_text(encoding="utf-8") == "aniccomhi\n"


def test_sandhi_file_manager_contributor_writes_own_file_only(
    tmp_path: Path,
) -> None:
    alice = make_paths(tmp_path, "alice")
    shared = make_paths(tmp_path, "1")
    toolkit: Any = SimpleNamespace(
        paths=alice, see_manager=None, variants=None, spelling_mistakes=None
    )

    manager = SandhiFileManager(toolkit)
    manager.add_sandhi_to_checked_csv("ekova")
    manager.update_sandhi_corrections_csv("aniccomhi", "anicco + amhi")

    assert alice.sandhi_checked_path.read_text(encoding="utf-8") == (
        "ekova\naniccomhi\n"
    )
    assert alice.sandhi_corrections_path.read_text(encoding="utf-8") == (
        "aniccomhi\tanicco + amhi\n"
    )
    assert not shared.sandhi_checked_path.exists()
    assert not shared.sandhi_corrections_path.exists()


def test_sandhi_ok_list_includes_own_words(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shared_checked = tmp_path / "shared_checked.csv"
    shared_checked.write_text("shared_word\n", encoding="utf-8")
    own_checked = tmp_path / "checked_alice.csv"
    own_checked.write_text("own_word\n", encoding="utf-8")
    stub = SimpleNamespace(decon_checked=shared_checked)
    monkeypatch.setattr("gui2.database_manager.ProjectPaths", lambda: stub)
    monkeypatch.setattr(DatabaseManager, "new_db_session", lambda self: None)

    assert DatabaseManager(own_checked).sandhi_ok_list == {"shared_word", "own_word"}
    assert DatabaseManager().sandhi_ok_list == {"shared_word"}
