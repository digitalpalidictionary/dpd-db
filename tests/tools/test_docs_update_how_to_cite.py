"""Tests for the generated How to Cite docs page."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import docs_update_how_to_cite as module
from tools.docs_update_how_to_cite import (
    EXAMPLE_ID,
    EXAMPLE_LEMMA,
    make_how_to_cite_md,
)

VERSION = "v0.4.20260905"


def test_page_names_the_current_version_everywhere() -> None:
    md = make_how_to_cite_md(VERSION)
    # once per citation form: whole dictionary, entry, Chicago, MLA, APA
    assert md.count(VERSION) >= 5


def test_page_uses_the_real_permalink() -> None:
    md = make_how_to_cite_md(VERSION)
    assert f"q={EXAMPLE_ID}" in md
    assert EXAMPLE_LEMMA in md


def test_doi_line_appears_only_when_known() -> None:
    assert "doi.org" not in make_how_to_cite_md(VERSION)
    assert "https://doi.org/10.5281/zenodo.1" in make_how_to_cite_md(
        VERSION, "10.5281/zenodo.1"
    )


def test_page_is_left_alone_on_an_ordinary_day(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Tracked file naming the released version — a dev build must not churn it."""

    page = tmp_path / "how_to_cite.md"
    page.write_text("committed contents", encoding="utf-8")
    _run_main(monkeypatch, page, uposatha=False)

    assert page.read_text(encoding="utf-8") == "committed contents"


def test_page_is_rewritten_on_an_uposatha(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    page = tmp_path / "how_to_cite.md"
    page.write_text("stale", encoding="utf-8")
    _run_main(monkeypatch, page, uposatha=True)

    assert VERSION in page.read_text(encoding="utf-8")


def _run_main(monkeypatch: pytest.MonkeyPatch, page: Path, *, uposatha: bool) -> None:
    monkeypatch.setattr(
        module.UposathaManger, "uposatha_today", classmethod(lambda cls: uposatha)
    )
    monkeypatch.setattr(module, "config_read", lambda *_: VERSION)
    monkeypatch.setattr(module, "get_doi", lambda: None)
    monkeypatch.setattr(
        module, "ProjectPaths", lambda: SimpleNamespace(docs_how_to_cite_md_path=page)
    )
    module.main()
