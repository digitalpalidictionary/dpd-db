"""Tests for the generated How to Cite docs page."""

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
