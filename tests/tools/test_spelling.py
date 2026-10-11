from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.spelling import CustomSpellChecker


@pytest.fixture(autouse=True)
def fresh_singleton() -> Iterator[None]:
    """The checker is a process-wide singleton, so reset it around each test."""
    CustomSpellChecker._instance = None
    CustomSpellChecker._initialized = False
    yield
    CustomSpellChecker._instance = None
    CustomSpellChecker._initialized = False


def make_checker(shared: Path, user_dict: Path | None) -> CustomSpellChecker:
    with patch("tools.spelling.ProjectPaths") as pp:
        pp.return_value = MagicMock(user_dict_path=shared)
        return CustomSpellChecker(user_dict)


def test_no_user_dict_writes_shared_file(tmp_path: Path) -> None:
    shared = tmp_path / "shared.txt"
    shared.write_text("alpha\n", encoding="utf-8")

    checker = make_checker(shared, None)
    checker.add_to_dictionary("zzqword")

    assert shared.read_text(encoding="utf-8") == "alpha\nzzqword\n"


def test_contributor_add_writes_only_own_file(tmp_path: Path) -> None:
    shared = tmp_path / "shared.txt"
    shared.write_text("alpha\n", encoding="utf-8")
    shared_before = shared.read_bytes()
    own = tmp_path / "user_dictionary_alice.txt"

    checker = make_checker(shared, own)
    checker.add_to_dictionary("zzqword")

    assert shared.read_bytes() == shared_before
    assert own.read_text(encoding="utf-8") == "zzqword\n"


def test_contributor_loads_shared_and_own_words(tmp_path: Path) -> None:
    shared = tmp_path / "shared.txt"
    shared.write_text("zzqshared\n", encoding="utf-8")
    own = tmp_path / "own.txt"
    own.write_text("zzqown\n", encoding="utf-8")

    checker = make_checker(shared, own)

    assert not checker.has_misspellings("zzqshared zzqown")
    assert checker.has_misspellings("zzqother")
