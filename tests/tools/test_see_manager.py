# -*- coding: utf-8 -*-
"""Tests for the SeeManager class."""

from tools.see_manager import SeeManager
from tools.paths import ProjectPaths


def test_see_manager_loads_empty_tsv(tmp_path):
    """Test that an empty TSV (header only) loads without error."""
    tsv = tmp_path / "see.tsv"
    tsv.write_text("see\theadword\n", encoding="utf-8")

    pth = ProjectPaths(base_dir=tmp_path, create_dirs=False)
    pth.see_path = tsv

    sm = SeeManager(pth=pth)
    assert sm.get_see_dict() == {}
    assert sm.headers == ["see", "headword"]


def test_see_manager_add_entry(tmp_path):
    """Test that update_and_save adds an entry and persists it."""
    tsv = tmp_path / "see.tsv"
    tsv.write_text("see\theadword\n", encoding="utf-8")

    pth = ProjectPaths(base_dir=tmp_path, create_dirs=False)
    pth.see_path = tsv

    sm = SeeManager(pth=pth)
    sm.update_and_save("karohi", "karoti")

    assert sm.get_see_dict() == {"karohi": "karoti"}

    # Verify it was written to disk
    content = tsv.read_text(encoding="utf-8")
    assert "karohi" in content
    assert "karoti" in content


def test_see_manager_update_entry(tmp_path):
    """Test that update_and_save overwrites an existing entry."""
    tsv = tmp_path / "see.tsv"
    tsv.write_text("see\theadword\nkarohi\tkaroti\n", encoding="utf-8")

    pth = ProjectPaths(base_dir=tmp_path, create_dirs=False)
    pth.see_path = tsv

    sm = SeeManager(pth=pth)
    sm.update_and_save("karohi", "kāreti")

    assert sm.get_see_dict()["karohi"] == "kāreti"


def test_see_manager_get_dict_returns_copy(tmp_path):
    """Test that get_see_dict returns a copy, not the original."""
    tsv = tmp_path / "see.tsv"
    tsv.write_text("see\theadword\nfoo\tbar\n", encoding="utf-8")

    pth = ProjectPaths(base_dir=tmp_path, create_dirs=False)
    pth.see_path = tsv

    sm = SeeManager(pth=pth)
    d1 = sm.get_see_dict()
    d2 = sm.get_see_dict()
    assert d1 is not d2
    assert d1 == d2


def test_see_manager_reload(tmp_path):
    """Test that load() re-reads the file after external modification."""
    tsv = tmp_path / "see.tsv"
    tsv.write_text("see\theadword\n", encoding="utf-8")

    pth = ProjectPaths(base_dir=tmp_path, create_dirs=False)
    pth.see_path = tsv

    sm = SeeManager(pth=pth)
    assert len(sm.get_see_dict()) == 0

    # Simulate external modification
    tsv.write_text("see\theadword\nexternalword\theadword1\n", encoding="utf-8")
    sm.load()
    assert sm.get_see_dict() == {"externalword": "headword1"}


def test_see_manager_missing_file(tmp_path):
    """Test that SeeManager handles a missing TSV file gracefully."""
    pth = ProjectPaths(base_dir=tmp_path, create_dirs=False)
    pth.see_path = tmp_path / "nonexistent.tsv"

    sm = SeeManager(pth=pth)
    assert sm.get_see_dict() == {}
