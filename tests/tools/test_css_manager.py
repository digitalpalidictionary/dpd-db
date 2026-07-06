"""Tests for tools.css_manager.CSSManager, focused on the file-read cache."""

from pathlib import Path

import pytest

from tools.css_manager import CSSManager


@pytest.fixture(autouse=True)
def _clear_css_cache():
    """Each test starts with an empty class-level cache."""
    CSSManager._css_cache.clear()
    yield
    CSSManager._css_cache.clear()


def test_two_instances_produce_identical_update_style() -> None:
    header = "<html><head><style>\n</style></head><body></body></html>"
    for style in ("primary", "secondary", "dpd", "root", "variants"):
        a = CSSManager().update_style(header, style)
        b = CSSManager().update_style(header, style)
        assert a == b


def test_css_files_read_once_across_instances(monkeypatch) -> None:
    reads: list[str] = []
    original = Path.read_text

    def counting_read_text(self, *args, **kwargs):
        reads.append(str(self))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counting_read_text)

    CSSManager()
    CSSManager()
    CSSManager()

    # three distinct CSS files, each read exactly once despite three instances
    assert len(reads) == 3
    assert len(set(reads)) == 3


def test_reduce_style_mutation_is_per_instance() -> None:
    """variables_reduced is mutated by reduce_style; the cache must not leak
    that mutation between instances."""
    a = CSSManager()
    a.reduce_style("primary")
    reduced = a.variables_reduced

    b = CSSManager()
    assert b.variables_reduced != reduced or "--primary" in reduced
    # a fresh instance sees the full, unreduced variables text
    assert b.variables_reduced == b.dpd_variables
