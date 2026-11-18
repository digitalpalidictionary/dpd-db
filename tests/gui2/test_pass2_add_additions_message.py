"""The additions button names the contributor who sent the loaded word."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import flet as ft
import pytest

from gui2.pass2_add_view import Pass2AddView

Queue = list[tuple[dict[str, str | int], Path | None, str, int]]


@pytest.fixture(autouse=True)
def _stub_page(monkeypatch: pytest.MonkeyPatch) -> None:
    # Flet 1.0 raises on `.page` of an unmounted control.
    monkeypatch.setattr(Pass2AddView, "page", MagicMock(), raising=False)


def _click_all(queue: Queue) -> list[str]:
    """Press the additions button once per queued word; return the messages."""
    messages: list[str] = []
    view = object.__new__(Pass2AddView)
    state = {
        "_reject_button": ft.Button("Reject", visible=False),
        "dpd_fields": SimpleNamespace(
            flags=SimpleNamespace(addition=False, correction=False),
            fields={},
            clear_fields=MagicMock(),
            update_add_fields=MagicMock(),
        ),
        "current_addition": None,
        "_current_addition_origin": None,
        "_current_addition_key": None,
        "_current_correction_origin": None,
        "_current_correction_key": None,
        "additions_manager": SimpleNamespace(
            get_next_addition=MagicMock(side_effect=queue)
        ),
        "update_message": messages.append,
    }
    for name, value in state.items():
        setattr(view, name, value)
    for _ in queue:
        view._click_additions_button(MagicMock())
    return messages


def test_each_loaded_word_names_its_own_contributor() -> None:
    # one queue merged from two contributors' files: the name follows the word
    messages = _click_all(
        [
            (
                {"id": 1, "lemma_1": "akakkasa"},
                Path("additions_panya.json"),
                "panya_1",
                1,
            ),
            (
                {"id": 2, "lemma_1": "dhammacakka"},
                Path("additions_alice.json"),
                "alice_2",
                0,
            ),
        ]
    )
    assert messages == [
        "panya: Loaded akakkasa. 1 additions remaining.",
        "alice: Loaded dhammacakka. 0 additions remaining.",
    ]


def test_an_addition_with_no_origin_file_is_named_primary() -> None:
    messages = _click_all([({"id": 3, "lemma_1": "one"}, None, "1_3", 0)])
    assert messages == ["primary: Loaded one. 0 additions remaining."]
