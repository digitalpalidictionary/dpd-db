"""Verify extraction-only passage preview formatting."""

from exporter.analysis.passage_by_code import PassageResult

import exporter.analysis.passage_extraction as passage_extraction
from exporter.analysis.passage_extraction import format_extraction_report


def test_format_extraction_report_numbers_prose_paragraphs() -> None:
    result = PassageResult(
        source="AN3.12",
        vagga="rathakāravaggo, sāraṇīyasuttaṃ",
        paragraphs=[
            "tīṇimāni, bhikkhave, rañño khattiyassa.",
            "puna caparaṃ, bhikkhave.",
        ],
        is_verse=False,
    )

    report = format_extraction_report(result)

    assert "Source: AN3.12" in report
    assert "Vagga/Sutta: rathakāravaggo, sāraṇīyasuttaṃ" in report
    assert "Units: 2 paragraphs" in report
    assert "## Paragraph 1" in report
    assert "tīṇimāni, bhikkhave" in report


def test_format_extraction_report_numbers_verses() -> None:
    result = PassageResult(
        source="DHP1",
        vagga="yamakavaggo",
        paragraphs=["manopubbaṅgamā dhammā"],
        is_verse=True,
    )

    report = format_extraction_report(result)

    assert "Units: 1 verse" in report
    assert "## Verse 1" in report


def test_main_creates_analysis_runtime_dirs(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        passage_extraction,
        "parse_args",
        lambda: type("Args", (), {"code": "DHP1"})(),
    )
    monkeypatch.setattr(
        passage_extraction,
        "ensure_analysis_dirs",
        lambda: calls.append("created"),
    )
    monkeypatch.setattr(
        passage_extraction,
        "get_passage_by_code",
        lambda _code: PassageResult(
            source="DHP1",
            vagga="yamakavaggo",
            paragraphs=["manopubbaṅgamā dhammā"],
            is_verse=True,
        ),
    )

    passage_extraction.main()

    assert calls == ["created"]
