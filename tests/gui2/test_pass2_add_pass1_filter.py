"""The Pass1 field filter of Pass2Add shows origin and survives a clear."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import flet as ft
import pytest

from gui2.pass2_add_view import Pass2AddView


@pytest.fixture(autouse=True)
def _stub_page(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Pass2AddView, "page", MagicMock(), raising=False)


def _view(filter_value: str) -> Pass2AddView:
    """Build the view without its __init__ (flet.Page + live dpd.db)."""
    view = object.__new__(Pass2AddView)
    view._filter_radios = SimpleNamespace(value=filter_value)  # pyright: ignore[reportAttributeAccessIssue]
    view._enter_id_or_lemma_field = ft.TextField()  # pyright: ignore[reportAttributeAccessIssue]
    view._reject_button = SimpleNamespace(visible=True)  # pyright: ignore[reportAttributeAccessIssue]
    view._top_section = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view._bottom_section = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view.update_message = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]

    def build() -> MagicMock:
        view.dpd_fields = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
        return MagicMock()

    view._build_middle_section = build  # pyright: ignore[reportAttributeAccessIssue]
    return view


def _shown_fields(view: Pass2AddView) -> list[str]:
    view.dpd_fields.filter_fields.assert_called_once()  # pyright: ignore[reportAttributeAccessIssue]
    return view.dpd_fields.filter_fields.call_args.args[0]  # pyright: ignore[reportAttributeAccessIssue]


def test_pass1_filter_shows_origin() -> None:
    view = _view("all")
    view.dpd_fields = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]

    view._handle_filter_change(SimpleNamespace(control=SimpleNamespace(value="pass1")))  # pyright: ignore[reportArgumentType]

    shown = _shown_fields(view)
    assert "origin" in shown
    assert "lemma_1" in shown


def test_clear_keeps_the_pass1_filter() -> None:
    view = _view("pass1")

    view.clear_all_fields()

    assert view._filter_radios.value == "pass1"
    assert "origin" in _shown_fields(view)


@pytest.mark.parametrize("name", ["root", "compound", "word"])
def test_clear_resets_the_other_filters(name: str) -> None:
    view = _view(name)

    view.clear_all_fields()

    assert view._filter_radios.value == "all"


def test_missing_words_popup_stays_closed_for_a_word_without_meaning_1() -> None:
    view = _view("pass1")
    view._missing_words_switch = SimpleNamespace(value=True)  # pyright: ignore[reportAttributeAccessIssue]
    view._find_missing_eg_words = MagicMock(  # pyright: ignore[reportAttributeAccessIssue]
        return_value=[("PARTS: a + b", {"a": {}})]
    )

    view._show_missing_words_dialog(SimpleNamespace(lemma_1="gacchati", meaning_1=""))  # pyright: ignore[reportArgumentType]

    view._find_missing_eg_words.assert_not_called()  # pyright: ignore[reportAttributeAccessIssue]
