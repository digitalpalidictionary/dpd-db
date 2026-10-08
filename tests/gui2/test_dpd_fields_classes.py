import asyncio
import inspect

import flet as ft
import pytest

import gui2.dpd_fields_classes
from gui2.dpd_fields_classes import (
    DpdTextField,
    get_last_focused_field,
    track_focus,
)


@pytest.fixture(autouse=True)
def _reset_tracker(monkeypatch):
    monkeypatch.setattr(gui2.dpd_fields_classes, "_last_focused_field", None)


class TestTrackFocus:
    def test_records_the_focused_field(self, monkeypatch):
        monkeypatch.setattr("gui2.dpd_fields_classes.is_mounted", lambda control: True)
        field = DpdTextField(name="lemma_1")
        handler = track_focus(field, None)

        handler(ft.Event(control=field, name="focus", data=""))

        assert get_last_focused_field() is field

    def test_still_calls_the_original_handler(self, monkeypatch):
        monkeypatch.setattr("gui2.dpd_fields_classes.is_mounted", lambda control: True)
        field = DpdTextField(name="lemma_1")
        calls: list[str] = []
        handler = track_focus(field, lambda e: calls.append("original"))

        handler(ft.Event(control=field, name="focus", data=""))

        assert calls == ["original"]
        assert get_last_focused_field() is field

    def test_unmounted_field_reads_as_none(self):
        """A field left focused in a form since rebuilt must not be restored."""
        field = DpdTextField(name="lemma_1")
        handler = track_focus(field, None)
        handler(ft.Event(control=field, name="focus", data=""))

        # The field was never mounted on a page, so it reads as stale.
        assert get_last_focused_field() is None

    def test_async_original_handler_is_awaited(self, monkeypatch):
        """Flet awaits only coroutine handlers, so the wrapper must stay async."""
        monkeypatch.setattr("gui2.dpd_fields_classes.is_mounted", lambda control: True)
        field = DpdTextField(name="meaning_1")
        calls: list[str] = []

        async def original(e: ft.ControlEvent) -> None:
            calls.append("original")

        handler = track_focus(field, original)
        assert inspect.iscoroutinefunction(handler)

        asyncio.run(handler(ft.Event(control=field, name="focus", data="")))

        assert calls == ["original"]
        assert get_last_focused_field() is field
