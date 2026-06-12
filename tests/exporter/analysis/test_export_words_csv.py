"""Test report source selection helpers for the word CSV exporter."""

from pathlib import Path

import pytest

from exporter.analysis import export_words_csv
from exporter.analysis.export_words_csv import (
    _available_report_choices,
    _clip_example_to_bold_context,
    _close_report_choices,
    _exact_report_choice,
    _get_vagga,
    _normalize_export_source,
    _parse_report,
    _prompt_profile,
    _resolve_report_path,
)


def test_available_report_choices_lists_selectable_sources(tmp_path: Path) -> None:
    (tmp_path / "SN12.3_p1_study.md").write_text("", encoding="utf-8")
    (tmp_path / "kn2_DHP1.md").write_text("", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("", encoding="utf-8")

    assert _available_report_choices(tmp_path) == [
        "kn2_DHP1",
        "SN12.3_p1",
    ]


def test_resolve_report_path_accepts_study_and_plain_markdown(
    tmp_path: Path,
) -> None:
    study_report = tmp_path / "SN12.3_p1_study.md"
    plain_report = tmp_path / "kn2_DHP1.md"
    study_report.write_text("", encoding="utf-8")
    plain_report.write_text("", encoding="utf-8")

    assert _resolve_report_path("SN12.3_p1", tmp_path) == study_report
    assert _resolve_report_path("SN12.3_p1_study", tmp_path) == study_report
    assert _resolve_report_path("kn2_DHP1", tmp_path) == plain_report


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("SN12.3_p1", "SN12.3_p1"),
        ("SN12.3_p1_study", "SN12.3_p1"),
        ("sn 12.3_p1", "SN12.3_p1"),
        ("KN2 dhp1", "kn2_DHP1"),
    ],
)
def test_exact_report_choice_accepts_suffix_case_and_spacing(
    tmp_path: Path,
    source: str,
    expected: str,
) -> None:
    (tmp_path / "SN12.3_p1_study.md").write_text("", encoding="utf-8")
    (tmp_path / "kn2_DHP1.md").write_text("", encoding="utf-8")

    assert _exact_report_choice(source, tmp_path) == expected


def test_close_report_choices_prefers_passage_parts_for_base_sutta(
    tmp_path: Path,
) -> None:
    (tmp_path / "SN12.1_p1_study.md").write_text("", encoding="utf-8")
    (tmp_path / "SN12.3_p1_study.md").write_text("", encoding="utf-8")
    (tmp_path / "AN3.12_p1_study.md").write_text("", encoding="utf-8")

    assert _close_report_choices("SN12.1", tmp_path) == ["SN12.1_p1"]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("SN12.3_p1", "SN12.3"),
        ("SN12.3_p1_study", "SN12.3"),
        ("TH15_study", "TH15"),
        ("DHP134", "DHP134"),
        ("SNP32", "SNP32"),
        ("AN2.1", "AN2.1"),
    ],
)
def test_normalize_export_source_returns_canonical_sutta_code(
    source: str,
    expected: str,
) -> None:
    assert _normalize_export_source(source) == expected


def test_parse_report_uses_blank_id_top_level_rows_as_component_parents() -> None:
    content = """# Analysis of: TH15

pañcasaṅgātigo bhikkhu,
oghatiṇṇo'ti vuccatī'ti.

### English Translation

### Word-by-Word Analysis

| ID | Word in Sentence | Grammar | Meaning | Construction | Root |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 49885 | bhikkhu | masc nom sg of bhikkhu | a monk | √bhikkh + u | √bhikkh |
|  | oghatiṇṇo'ti | sandhi | one who has crossed, thus | oghatiṇṇo + iti |  |
| 18416 | - oghatiṇṇo | masc nom sg of oghatiṇṇa | crossed over | oghaṃ + tiṇṇa |  |
| 18411 | - - oghaṃ | masc acc sg of ogha | flood |  |  |
| 30559 | - - tiṇṇa | pp | crossed | √tar + na | √tar |
| 13466 | - iti | ind | thus |  |  |
|  | vuccatī'ti | sandhi | is called, thus | vuccati + iti |  |
| 69965 | - vuccati | pr 3rd sg of vuccati | is called | √vac + ya + ti | √vac |
"""

    _passage, rows = _parse_report(content)

    assert rows == [
        (49885, "bhikkhu", "bhikkhu", False),
        (18416, "oghatiṇṇo", "oghatiṇṇo'ti", True),
        (18411, "oghaṃ", "oghatiṇṇo", True),
        (30559, "tiṇṇa", "oghatiṇṇo", False),
        (13466, "iti", "oghatiṇṇo'ti", False),
        (69965, "vuccati", "vuccatī'ti", True),
    ]


def test_clip_example_to_bold_context_keeps_one_prose_sentence() -> None:
    example = (
        "first sentence has word. "
        "middle sentence has <b>word</b> here. "
        "last sentence has word again."
    )

    assert _clip_example_to_bold_context(example) == (
        "middle sentence has <b>word</b> here."
    )


def test_clip_example_to_bold_context_keeps_first_bolded_prose_sentence_only() -> None:
    example = (
        "first sentence has <b>word</b>. "
        "second sentence has <b>word</b> too. "
        "third sentence has no match."
    )

    assert _clip_example_to_bold_context(example) == "first sentence has <b>word</b>."


def test_clip_example_to_bold_context_keeps_four_gatha_lines() -> None:
    example = "\n".join(
        [
            "line one",
            "line two",
            "line three with <b>word</b>",
            "line four",
            "line five",
            "line six",
        ]
    )

    assert _clip_example_to_bold_context(example) == "\n".join(
        [
            "line two",
            "line three with <b>word</b>",
            "line four",
            "line five",
        ]
    )


def test_clip_example_to_bold_context_keeps_short_gatha() -> None:
    example = "\n".join(
        [
            "line one",
            "line two with <b>word</b>",
            "line three",
        ]
    )

    assert _clip_example_to_bold_context(example) == example


def test_get_vagga_uses_canonical_source_for_gathas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_get_passage_by_code(source: str) -> object:
        calls.append(source)
        return type("Passage", (), {"vagga": "paṭhamavaggo, pañcagāthā"})()

    monkeypatch.setattr(
        export_words_csv, "get_passage_by_code", fake_get_passage_by_code
    )

    assert _get_vagga("TH15_study") == "paṭhamavaggo, pañcagāthā"
    assert calls == ["TH15"]


@pytest.mark.parametrize(
    ("choice", "expected_profile"),
    [
        ("1", "basic"),
        ("2", "advanced"),
        ("3", "custom"),
        ("basic", "basic"),
        ("advanced", "advanced"),
        ("custom", "custom"),
    ],
)
def test_prompt_profile_accepts_numbers_and_names(
    monkeypatch: pytest.MonkeyPatch,
    choice: str,
    expected_profile: str,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: choice)

    assert _prompt_profile() == export_words_csv.PRESETS.get(
        expected_profile,
        export_words_csv.CUSTOM,
    )
