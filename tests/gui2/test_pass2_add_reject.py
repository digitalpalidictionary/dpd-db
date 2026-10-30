"""The Reject button in Pass2Add: shown for a loaded contributor entry only."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import flet as ft
import pytest

from gui2.pass2_add_view import Pass2AddView


@pytest.fixture(autouse=True)
def _stub_page(monkeypatch: pytest.MonkeyPatch) -> None:
    # Flet 1.0 raises on `.page` of an unmounted control.
    monkeypatch.setattr(Pass2AddView, "page", MagicMock(), raising=False)


def _view(**state: object) -> Pass2AddView:
    view = object.__new__(Pass2AddView)
    view._reject_button = ft.Button("Reject", visible=False)  # pyright: ignore[reportAttributeAccessIssue]
    view.dpd_fields = SimpleNamespace(  # pyright: ignore[reportAttributeAccessIssue]
        flags=SimpleNamespace(addition=False, correction=False)
    )
    view.current_addition = None  # pyright: ignore[reportAttributeAccessIssue]
    view.current_correction = None  # pyright: ignore[reportAttributeAccessIssue]
    view._current_addition_origin = None  # pyright: ignore[reportAttributeAccessIssue]
    view._current_addition_key = None  # pyright: ignore[reportAttributeAccessIssue]
    view._current_correction_origin = None  # pyright: ignore[reportAttributeAccessIssue]
    view._current_correction_key = None  # pyright: ignore[reportAttributeAccessIssue]
    view.additions_manager = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view.corrections_manager = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view.update_message = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view.clear_all_fields = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    for name, value in state.items():
        if name in ("addition", "correction"):
            setattr(view.dpd_fields.flags, name, value)
        else:
            setattr(view, name, value)
    return view


def test_hidden_when_nothing_is_loaded() -> None:
    view = _view()
    view._show_reject_if_contributor_entry()
    assert view._reject_button.visible is False


def test_shown_for_a_loaded_contributor_addition() -> None:
    view = _view(
        addition=True,
        _current_addition_origin=Path("additions_alice.json"),
        _current_addition_key="alice_1",
    )
    view._show_reject_if_contributor_entry()
    assert view._reject_button.visible is True


def test_hidden_for_an_entry_with_no_contributor_origin() -> None:
    view = _view(correction=True)
    view._show_reject_if_contributor_entry()
    assert view._reject_button.visible is False


def test_reject_an_addition_calls_the_additions_manager() -> None:
    entry = {"id": 1, "lemma_1": "one"}
    origin = Path("additions_alice.json")
    view = _view(
        addition=True,
        current_addition=entry,
        _current_addition_origin=origin,
        _current_addition_key="alice_1",
    )

    view._click_reject(MagicMock())

    view.additions_manager.reject.assert_called_once_with(origin, "alice_1", entry)  # pyright: ignore[reportAttributeAccessIssue]
    view.corrections_manager.reject.assert_not_called()  # pyright: ignore[reportAttributeAccessIssue]
    view.clear_all_fields.assert_called_once()  # pyright: ignore[reportAttributeAccessIssue]


def test_reject_a_correction_calls_the_corrections_manager() -> None:
    entry = {"id": 1, "lemma_1": "one"}
    origin = Path("corrections_alice.json")
    view = _view(
        correction=True,
        current_correction=entry,
        _current_correction_origin=origin,
        _current_correction_key="alice_1",
    )

    view._click_reject(MagicMock())

    view.corrections_manager.reject.assert_called_once_with(origin, "alice_1", entry)  # pyright: ignore[reportAttributeAccessIssue]
    view.additions_manager.reject.assert_not_called()  # pyright: ignore[reportAttributeAccessIssue]


def test_reject_does_nothing_without_a_loaded_entry() -> None:
    view = _view()

    view._click_reject(MagicMock())

    view.additions_manager.reject.assert_not_called()  # pyright: ignore[reportAttributeAccessIssue]
    view.corrections_manager.reject.assert_not_called()  # pyright: ignore[reportAttributeAccessIssue]
    view.clear_all_fields.assert_not_called()  # pyright: ignore[reportAttributeAccessIssue]


def test_a_failed_reject_keeps_the_form() -> None:
    view = _view(
        addition=True,
        current_addition={"id": 1},
        _current_addition_origin=Path("additions_alice.json"),
        _current_addition_key="alice_1",
    )
    view.additions_manager.reject.side_effect = OSError("disk full")  # pyright: ignore[reportAttributeAccessIssue]

    view._click_reject(MagicMock())

    view.clear_all_fields.assert_not_called()  # pyright: ignore[reportAttributeAccessIssue]
    assert "disk full" in view.update_message.call_args.args[0]  # pyright: ignore[reportAttributeAccessIssue]
