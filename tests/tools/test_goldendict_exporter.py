"""Regression tests for the pyglossary cacheDir/tmp cleanup race.

Background: when two ``Glossary`` instances are created in the same export
(glos-outer in ``export_to_goldendict_with_pyglossary``, glos-inner inside
``write_to_slob``), both ``newDataEntry`` calls fall back to the shared
``cacheDir/tmp`` directory before ``write()`` runs. Both glossaries add that
shared path to their separate ``_cleanupPathList`` sets, so the first
``cleanup()`` rmtrees it and the second logs a spurious
``no such file or directory`` error.

The fix in ``create_glossary()`` accesses ``glos.tmpDataDir`` immediately after
construction, forcing a per-glossary ``cacheDir/<uuid>_res`` dir so each
glossary cleans up its own unique path.
"""

from pathlib import Path

import pytest

import tools.goldendict_exporter as goldendict_exporter
from tools.goldendict_exporter import DictInfo, create_glossary


def _make_dict_info() -> DictInfo:
    """Build a minimal DictInfo for tests."""
    return DictInfo(
        bookname="test-dict",
        author="test-author",
        description="test-description",
        website="https://example.test",
        source_lang="pi",
        target_lang="en",
    )


def test_create_glossary_has_nonempty_tmp_dir() -> None:
    """create_glossary() must give the glossary a per-glossary tmp dir.

    Without the ``glos.tmpDataDir`` access, ``_tmpDataDir`` stays empty and
    ``newDataEntry`` falls back to the shared ``cacheDir/tmp``.
    """
    glos = create_glossary(_make_dict_info())
    tmp_dir = glos.tmpDataDir
    assert tmp_dir
    assert Path(tmp_dir).name.endswith("_res")


def test_two_glossaries_have_distinct_tmp_dirs() -> None:
    """Two separately-created glossaries must not share a tmp dir.

    The whole point of the fix: each glossary gets its own
    ``cacheDir/<uuid>_res`` dir, so cleanup() on one never races with the
    other's rmtree of a shared ``cacheDir/tmp``.
    """
    glos_a = create_glossary(_make_dict_info())
    glos_b = create_glossary(_make_dict_info())
    assert glos_a.tmpDataDir != glos_b.tmpDataDir


def test_glossary_tmp_dir_is_not_shared_cache_dir_tmp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The per-glossary tmp dir must not be the shared cacheDir/tmp fallback.

    pyglossary's ``newDataEntry`` uses ``join(cacheDir, "tmp")`` when
    ``_tmpDataDir`` is empty. The fix must ensure ``_tmpDataDir`` is set to a
    unique ``cacheDir/<uuid>_res`` path instead.
    """
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cache_tmp = tmp_path / "pyglossary" / "tmp"
    glos = create_glossary(_make_dict_info())
    assert Path(glos.tmpDataDir) != cache_tmp


def test_create_glossary_fix_is_present() -> None:
    """Guard: the side-effect access must remain in create_glossary().

    If a future refactor drops the ``glos.tmpDataDir`` access, the cleanup
    race returns. This test fails to remind whoever touched the function.
    """
    source = Path(goldendict_exporter.__file__).read_text(encoding="utf-8")
    assert "glos.tmpDataDir" in source
