"""The missing-words popup must not leave recursive global keyboard state.

The popup used to install a page-level keyboard handler that delegated
unhandled keys to "the handler I replaced", looked up through a mutable
instance attribute rather than captured at install time. Once that attribute
held the popup's own handler, every keypress delegated to itself until the
stack blew.
"""

import asyncio
from types import SimpleNamespace
from typing import Any

import flet as ft
import pytest

from gui2.pass2_add_view import Pass2AddView


class FakePage:
    """The slice of ft.Page the popup touches, plus a real dialog stack."""

    def __init__(self) -> None:
        self.on_keyboard_event = self._original_kb
        self.dialogs: list[Any] = []
        self.updates: int = 0

    async def _original_kb(self, e: ft.KeyboardEvent) -> None:
        """Stands in for the app's global keyboard handler, which is async."""
        self.original_kb_calls = getattr(self, "original_kb_calls", 0) + 1

    def show_dialog(self, dialog: Any) -> None:
        if dialog in self.dialogs:
            raise RuntimeError("Dialog is already opened")
        dialog.open = True
        self.dialogs.append(dialog)

    def pop_dialog(self) -> Any | None:
        dialog = next((d for d in reversed(self.dialogs) if d.open), None)
        if dialog is None:
            return None
        dialog.open = False
        self.dialogs.remove(dialog)
        return dialog

    def update(self) -> None:
        self.updates += 1


@pytest.fixture(autouse=True)
def settable_page(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flet 1.0 made `Control.page` a read-only property that walks the tree.

    The popup only ever reads it, so the tests hand it a fake through a plain
    attribute instead of mounting a real page.
    """
    monkeypatch.setattr(
        Pass2AddView, "page", property(lambda self: self._test_page), raising=False
    )


def _view() -> tuple[Pass2AddView, FakePage]:
    """Build the view without its __init__ (flet.Page + live dpd.db)."""
    view = object.__new__(Pass2AddView)
    page = FakePage()
    view._test_page = page  # pyright: ignore[reportAttributeAccessIssue]
    view._missing_words_switch = SimpleNamespace(value=True)  # pyright: ignore[reportAttributeAccessIssue]
    # Keyed off the saved word so two opens build dialogs with different
    # content: flet's dialog stack compares controls by value, so identical
    # popups would collide before the behaviour under test is reached.
    view._find_missing_eg_words = lambda w: [  # pyright: ignore[reportAttributeAccessIssue]
        (f"from example_1 of {w.lemma_1}", {f"missing_{w.lemma_1}": {"comment": "eg"}})
    ]
    view._eg_saved_kb = None  # pyright: ignore[reportAttributeAccessIssue]
    view._eg_alert = None  # pyright: ignore[reportAttributeAccessIssue]
    return view, page


def _key(key: str) -> ft.KeyboardEvent:
    return ft.KeyboardEvent(
        name="keyboard_event",
        control=None,  # pyright: ignore[reportArgumentType]
        key=key,
        shift=False,
        ctrl=False,
        alt=False,
        meta=False,
    )


async def _press(page: FakePage, name: str) -> None:
    handler = page.on_keyboard_event
    if handler is None:
        return
    result = handler(_key(name))
    if asyncio.iscoroutine(result):
        await result


class TestNoRecursiveKeyboardState:
    def test_opening_the_popup_twice_does_not_recurse(self) -> None:
        view, page = _view()

        view._show_missing_words_dialog(SimpleNamespace(lemma_1="gacchati"))  # pyright: ignore[reportArgumentType]
        view._show_missing_words_dialog(SimpleNamespace(lemma_1="karoti"))  # pyright: ignore[reportArgumentType]

        # A key the popup does not consume: this is where the old handler
        # delegated to itself.
        asyncio.run(_press(page, "Escape"))

    def test_global_keyboard_handler_is_left_alone(self) -> None:
        view, page = _view()
        original = page.on_keyboard_event

        view._show_missing_words_dialog(SimpleNamespace(lemma_1="gacchati"))  # pyright: ignore[reportArgumentType]

        assert page.on_keyboard_event is original, (
            "the popup replaced the app's global keyboard handler; closing it "
            "now depends on restoring that handler correctly"
        )


class TestDialogStack:
    def test_closing_removes_the_dialog_from_the_stack(self) -> None:
        view, page = _view()
        headword = SimpleNamespace(lemma_1="gacchati")

        view._show_missing_words_dialog(headword)  # pyright: ignore[reportArgumentType]
        assert len(page.dialogs) == 1

        view._close_eg_alert()

        assert page.dialogs == [], (
            f"closed dialogs are piling up on the page's dialog stack: {page.dialogs}"
        )

    def test_reopening_after_close_is_possible(self) -> None:
        view, page = _view()

        for lemma in ("gacchati", "karoti", "bhavati"):
            view._show_missing_words_dialog(SimpleNamespace(lemma_1=lemma))  # pyright: ignore[reportArgumentType]
            view._close_eg_alert()

        assert page.dialogs == []


if __name__ == "__main__":
    pytest.main([__file__])
