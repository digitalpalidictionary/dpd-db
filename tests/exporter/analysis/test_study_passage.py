"""Verify Stage 1 passage preview truncation and multi-select parsing."""

from pathlib import Path
from types import SimpleNamespace

import pytest

import exporter.analysis.study_passage as study_passage
from exporter.analysis.passage_extraction import format_extraction_report
from exporter.analysis.passage_by_code import PassageResult
from exporter.analysis.paths import AnalysisDirs
from exporter.analysis.study_passage import (
    _build_raw_responses_log,
    _format_selection_preview,
    _parse_args,
    _parse_selection_indices,
    _select_passage,
)


def test_format_selection_preview_truncates_long_units() -> None:
    result = PassageResult(
        source="AN3.12",
        vagga="rathakāravaggo, sāraṇīyasuttaṃ",
        paragraphs=[
            "one two three four five six seven eight nine ten eleven twelve "
            "thirteen fourteen",
        ],
        is_verse=False,
    )

    preview = _format_selection_preview(result)

    assert (
        "## Paragraph 1 (14 words): one two three four five six seven eight "
        "nine ten eleven twelve…"
    ) in preview
    assert "thirteen fourteen" not in preview


def test_format_selection_preview_keeps_short_units_untruncated() -> None:
    result = PassageResult(
        source="DHP1",
        vagga="yamakavaggo",
        paragraphs=["one two three"],
        is_verse=True,
    )

    preview = _format_selection_preview(result)

    assert "## Verse 1 (3 words): one two three" in preview
    assert "…" not in preview


def test_format_selection_preview_header_matches_extraction_preview() -> None:
    result = PassageResult(
        source="AN3.12",
        vagga="rathakāravaggo, sāraṇīyasuttaṃ",
        paragraphs=[
            "tīṇimāni, bhikkhave, rañño khattiyassa.",
            "puna caparaṃ, bhikkhave.",
        ],
        is_verse=False,
    )

    selection_header = _format_selection_preview(result).splitlines()[:3]
    extraction_header = format_extraction_report(result).splitlines()[:3]

    assert selection_header == extraction_header


def test_parse_selection_indices_supports_ranges_and_mixed_input() -> None:
    assert _parse_selection_indices("1-2 5", 6) == [0, 1, 4]
    assert _parse_selection_indices("3 5", 6) == [2, 4]
    assert _parse_selection_indices("3-5", 6) == [2, 3, 4]


def test_parse_selection_indices_rejects_out_of_bounds_values() -> None:
    assert _parse_selection_indices("0 2", 4) is None
    assert _parse_selection_indices("2-5", 4) is None
    assert _parse_selection_indices("x", 4) is None


def test_parse_args_requires_provider_and_model_together() -> None:
    args = _parse_args([])

    assert args.provider is None
    assert args.model is None
    with pytest.raises(SystemExit):
        _parse_args(["--provider", "p"])
    with pytest.raises(SystemExit):
        _parse_args(["--model", "m"])

    args = _parse_args(["--provider", "p", "--model", "m"])

    assert args.provider == "p"
    assert args.model == "m"


def test_build_raw_responses_log_includes_chunk_requests() -> None:
    log = _build_raw_responses_log(
        "SN15.1_p2",
        {
            "chunk_requests": [
                {
                    "status_message": "first ok",
                    "raw_response": '{"scores": {}}',
                    "reformat_status_message": "reformat ok",
                    "reformat_raw_response": '{"scores": {"1_0": {"score": 10}}}',
                    "translation_status_message": "translation ok",
                    "translation_raw_response": '{"translation": "T"}',
                }
            ],
            "retry_requests": [
                {
                    "status_message": "retry ok",
                    "raw_response": '{"scores": {"2_0": {"score": 10}}}',
                }
            ],
        },
    )

    assert "## First response" not in log
    assert "## Chunk 1 first response" in log
    assert "Status: first ok" in log
    assert "## Chunk 1 reformat response" in log
    assert "## Chunk 1 translation response (word→key map path)" in log
    assert "## Retry 1 (missing scores)" in log


def test_write_ai_debug_artifacts_writes_json_and_raw(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    reports_dir = tmp_path / "reports"
    output_dir.mkdir()
    reports_dir.mkdir()

    study_passage._write_ai_debug_artifacts(
        "TH1",
        {"raw_response": "partial", "status_message": "failed status"},
        include_raw=True,
        output_dir=output_dir,
        reports_dir=reports_dir,
    )

    assert (output_dir / "TH1_ai_debug.json").read_text(encoding="utf-8") == (
        '{\n  "raw_response": "partial",\n  "status_message": "failed status"\n}'
    )
    assert "partial" in (reports_dir / "TH1_ai_raw.txt").read_text(encoding="utf-8")


def test_main_writes_debug_artifacts_when_translate_sentence_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_dir = tmp_path / "output"
    reports_dir = tmp_path / "reports"
    output_dir.mkdir()
    reports_dir.mkdir()
    db_path = tmp_path / "dpd.db"
    db_path.touch()

    class StubSession:
        closed = False

        def close(self) -> None:
            self.closed = True

    class StubAIManager:
        pass

    session = StubSession()

    def fail_translate_sentence(*args, **kwargs):
        debug = kwargs["debug"]
        debug["raw_response"] = "partial"
        debug["status_message"] = "failed status"
        raise ValueError("boom")

    monkeypatch.setattr(
        study_passage,
        "_parse_args",
        lambda: SimpleNamespace(debug=True, provider=None, model=None),
    )
    monkeypatch.setattr(
        study_passage,
        "ProjectPaths",
        lambda: SimpleNamespace(dpd_db_path=db_path),
    )
    monkeypatch.setattr(
        study_passage,
        "get_passage_by_code",
        lambda _code: PassageResult(
            source="TH1",
            vagga="test vagga",
            paragraphs=["ekaṃ pāḷi"],
            is_verse=True,
        ),
    )
    monkeypatch.setattr("builtins.input", lambda _: "TH1")
    monkeypatch.setattr(study_passage, "get_db_session", lambda _path: session)
    monkeypatch.setattr(study_passage, "AIManager", StubAIManager)
    monkeypatch.setattr(
        study_passage,
        "translate_sentence",
        fail_translate_sentence,
    )
    monkeypatch.setattr(
        study_passage,
        "ensure_analysis_dirs",
        lambda: AnalysisDirs(
            root=tmp_path,
            input_dir=tmp_path / "input",
            reports_dir=reports_dir,
            output_dir=output_dir,
        ),
    )

    with pytest.raises(ValueError, match="boom"):
        study_passage.main()

    assert session.closed is True
    assert (output_dir / "TH1_ai_debug.json").exists()
    assert (reports_dir / "TH1_ai_raw.txt").exists()


def test_select_passage_returns_joined_mixed_selection(
    monkeypatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "1-2 4")

    result = PassageResult(
        source="AN3.12",
        vagga="rathakāravaggo, sāraṇīyasuttaṃ",
        paragraphs=[
            "paragraph one",
            "paragraph two",
            "paragraph three",
            "paragraph four",
        ],
        is_verse=False,
    )
    passage, suffix = _select_passage(result)

    assert passage == "paragraph one\nparagraph two\nparagraph four"
    assert suffix == "_p1-2-4"


def test_select_passage_falls_back_to_all_on_invalid_input(
    monkeypatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "1-9")

    result = PassageResult(
        source="AN3.12",
        vagga="rathakāravaggo, sāraṇīyasuttaṃ",
        paragraphs=[
            "paragraph one",
            "paragraph two",
        ],
        is_verse=False,
    )
    passage, suffix = _select_passage(result)

    assert passage == "paragraph one\nparagraph two"
    assert suffix == ""
