"""A refused clipboard copy must not stop a Pass2Add save."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import flet as ft
import pytest

from gui2.pass2_add_view import Pass2AddView


class _Clipboard:
    """Stands in for ft.Clipboard. The class attribute decides the outcome."""

    fail: bool = False
    copied: list[str] = []

    async def set(self, value: str) -> None:
        if self.fail:
            raise RuntimeError(
                "PlatformException(copy_fail, Clipboard.setData failed.)"
            )
        _Clipboard.copied.append(value)


@pytest.fixture(autouse=True)
def _fake_clipboard(monkeypatch: pytest.MonkeyPatch) -> None:
    _Clipboard.fail = False
    _Clipboard.copied = []
    monkeypatch.setattr(ft, "Clipboard", _Clipboard)


@pytest.fixture(autouse=True)
def _stub_page(monkeypatch: pytest.MonkeyPatch) -> None:
    # Flet 1.0 raises on `.page` of an unmounted control.
    monkeypatch.setattr(Pass2AddView, "page", MagicMock(), raising=False)


def _view() -> Pass2AddView:
    return object.__new__(Pass2AddView)


def test_copy_lemma_returns_true_and_copies() -> None:
    assert asyncio.run(_view()._copy_lemma("kata 1")) is True
    assert _Clipboard.copied == ["kata 1"]


def test_copy_lemma_returns_false_when_the_browser_refuses() -> None:
    _Clipboard.fail = True
    assert asyncio.run(_view()._copy_lemma("kata 1")) is False
    assert _Clipboard.copied == []


def _x_view(copied: bool) -> Pass2AddView:
    """A view that can run _click_x_button for a queued word with no id."""
    view = _view()
    view._x_manager = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view._x_manager.get_next.return_value = ("kata", {"comment": "from X"})
    view._x_manager.remaining_count.return_value = 4
    view.clear_all_fields = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view.dpd_fields = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view.dpd_fields.fields = {}
    view.add_headword_to_examples_and_commentary = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view.update_message = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view._copy_lemma = AsyncMock(return_value=copied)  # pyright: ignore[reportAttributeAccessIssue]
    return view


def test_x_button_message_says_copied_when_the_copy_worked() -> None:
    view = _x_view(copied=True)

    asyncio.run(view._click_x_button(MagicMock()))

    view.update_message.assert_called_once_with("[4] kata: from X (lemma_1 copied)")  # pyright: ignore[reportAttributeAccessIssue]


def test_x_button_message_says_not_copied_when_the_browser_refused() -> None:
    view = _x_view(copied=False)

    asyncio.run(view._click_x_button(MagicMock()))

    view.update_message.assert_called_once_with(  # pyright: ignore[reportAttributeAccessIssue]
        "[4] kata: from X (lemma_1 NOT copied: clipboard blocked)"
    )
