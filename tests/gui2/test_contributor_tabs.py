import logging

import pytest

from gui2.contributor_tabs import allowed_tabs, resolve_extra_tabs

ALL_LABELS = [
    "Global",
    "Transl",
    "Pass1Auto",
    "Pass1Add",
    "Pass2Pre",
    "Pass2x",
    "Pass2Auto",
    "Pass2Add",
    "'",
    "Sp",
    "Sandhi",
    "DB",
    "Tests",
    "Bold Search",
    "√",
    "CT",
    "Infl",
]


def labels(indices: list[int]) -> list[str]:
    return [ALL_LABELS[i] for i in indices]


def test_base_only() -> None:
    visible, read_only = allowed_tabs(ALL_LABELS, [])
    assert labels(visible) == ["Pass1Auto", "Pass1Add"]
    assert read_only == set()


def test_base_safe_and_read() -> None:
    visible, read_only = allowed_tabs(ALL_LABELS, ["DB", "Bold Search", "Transl"])
    assert labels(visible) == ["Transl", "Pass1Auto", "Pass1Add", "DB", "Bold Search"]
    assert labels(sorted(read_only)) == ["DB"]


def test_indices_are_original_positions() -> None:
    visible, read_only = allowed_tabs(ALL_LABELS, ["Infl", "√"])
    assert visible == [2, 3, 14, 16]
    assert read_only == {14, 16}


def test_hidden_and_unknown_labels_dropped_with_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        visible, read_only = allowed_tabs(ALL_LABELS, ["Pass2Add", "Typo", "DB"])
    assert labels(visible) == ["Pass1Auto", "Pass1Add", "DB"]
    assert read_only == {11}
    assert "Pass2Add" in caplog.text
    assert "Typo" in caplog.text


def test_resolve_empty_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DPD_GUI2_TABS", "")
    assert resolve_extra_tabs() == []
    monkeypatch.delenv("DPD_GUI2_TABS")
    assert resolve_extra_tabs() == []


def test_resolve_strips_blanks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DPD_GUI2_TABS", " Bold Search , DB ,,")
    assert resolve_extra_tabs() == ["Bold Search", "DB"]
