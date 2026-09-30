"""Tests for exporter/pdf/pdf_exporter.py."""

import pytest

from exporter.pdf import pdf_exporter


def test_front_matter_citation_carries_the_doi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pdf_exporter, "get_db_session", lambda _: None)
    monkeypatch.setattr(pdf_exporter, "config_read", lambda *_: "v0.4.20260905")

    citation = pdf_exporter.GlobalVars().citation

    assert "v0.4.20260905" in citation
    assert citation.endswith("https://doi.org/10.5281/zenodo.22979413")
