"""A contributor's variant / spelling-mistake flags go to their own file and
are read on top of the shared file."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from gui2.spelling import SpellingMistakesFileManager
from gui2.variants import VariantReadingFileManager

SHARED_VARIANTS = "variant\tmain\nshared_v\tshared_main\n"
SHARED_SPELLING = "mistake\tcorrection\nshared_m\tshared_c\n"


@pytest.fixture
def shared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Point every ProjectPaths the two managers build at a temp shared dir."""
    variants = tmp_path / "shared_variants.tsv"
    spelling = tmp_path / "shared_spelling.tsv"
    variants.write_text(SHARED_VARIANTS, encoding="utf-8")
    spelling.write_text(SHARED_SPELLING, encoding="utf-8")
    stub = SimpleNamespace(
        variant_readings_path=variants, spelling_mistakes_path=spelling
    )
    monkeypatch.setattr("gui2.variants.ProjectPaths", lambda: stub)
    monkeypatch.setattr("tools.variants_manager.ProjectPaths", lambda: stub)
    monkeypatch.setattr("gui2.spelling.ProjectPaths", lambda: stub)
    return SimpleNamespace(variants=variants, spelling=spelling)


def test_variant_contributor_writes_only_own_file(
    shared: SimpleNamespace, tmp_path: Path
) -> None:
    own = tmp_path / "variant_readings_alice.tsv"
    manager = VariantReadingFileManager(own)

    manager.update_and_save("new_v", "new_main")

    assert shared.variants.read_text(encoding="utf-8") == SHARED_VARIANTS
    assert own.read_text(encoding="utf-8") == "variant\tmain\nnew_v\tnew_main\n"


def test_variant_contributor_reads_shared_and_own(
    shared: SimpleNamespace, tmp_path: Path
) -> None:
    own = tmp_path / "variant_readings_alice.tsv"
    own.write_text("variant\tmain\nown_v\town_main\n", encoding="utf-8")

    manager = VariantReadingFileManager(own)

    assert manager.variants_dict == {
        "shared_v": "shared_main",
        "own_v": "own_main",
    }


def test_variant_user_one_still_writes_shared_file(shared: SimpleNamespace) -> None:
    manager = VariantReadingFileManager()

    manager.update_and_save("new_v", "new_main")

    assert shared.variants.read_text(encoding="utf-8") == (
        "variant\tmain\nshared_v\tshared_main\nnew_v\tnew_main\n"
    )


def test_spelling_contributor_writes_only_own_file(
    shared: SimpleNamespace, tmp_path: Path
) -> None:
    own = tmp_path / "spelling_mistakes_alice.tsv"
    manager = SpellingMistakesFileManager(own)

    manager.update_and_save("new_m", "new_c")

    assert shared.spelling.read_text(encoding="utf-8") == SHARED_SPELLING
    assert own.read_text(encoding="utf-8") == "mistake\tcorrection\nnew_m\tnew_c\n"


def test_spelling_contributor_reads_shared_and_own(
    shared: SimpleNamespace, tmp_path: Path
) -> None:
    own = tmp_path / "spelling_mistakes_alice.tsv"
    own.write_text("mistake\tcorrection\nown_m\town_c\n", encoding="utf-8")

    manager = SpellingMistakesFileManager(own)

    assert manager.spelling_mistakes_dict == {
        "shared_m": "shared_c",
        "own_m": "own_c",
    }


def test_spelling_user_one_still_writes_shared_file(shared: SimpleNamespace) -> None:
    manager = SpellingMistakesFileManager()

    manager.update_and_save("new_m", "new_c")

    assert shared.spelling.read_text(encoding="utf-8") == (
        "mistake\tcorrection\nshared_m\tshared_c\nnew_m\tnew_c\n"
    )
