"""Pass1Add must offer AI output as `_add` suggestions, never fill the fields."""

from types import SimpleNamespace

import pytest

import gui2.pass1_add_controller as controller_module
from gui2.pass1_add_controller import Pass1AddController

AI_DATA = {
    "lemma_1": "narena",
    "pos": "masc",
    "meaning_2": "man; person",
    "comment": "[deepseek: v4] instrumental",
}
SOURCE_TEXT_DATA = {
    "example_1": "narena kataṃ",
    "translation_1": "done by a man",
    "example_2": "naro gacchati",
    "translation_2": "the man goes",
}
FIELD_NAMES = list(AI_DATA) + list(SOURCE_TEXT_DATA)


class FakeDpdFields:
    def __init__(self) -> None:
        self.fields = {name: SimpleNamespace(value=None) for name in FIELD_NAMES}
        self.add_calls: list[dict[str, str]] = []

    def update_add_fields(self, data: dict[str, str]) -> None:
        self.add_calls.append(dict(data))


@pytest.fixture
def dpd_fields(monkeypatch: pytest.MonkeyPatch) -> FakeDpdFields:
    """Load one Pass1Auto entry into a fake view and return its fields."""
    monkeypatch.setattr(controller_module, "open_in_goldendict", lambda _: None)
    monkeypatch.setattr(controller_module.pyperclip, "copy", lambda _: None)

    fake_fields = FakeDpdFields()
    ctrl = object.__new__(Pass1AddController)
    ctrl.ui = SimpleNamespace(  # pyright: ignore[reportAttributeAccessIssue]
        word_in_text=SimpleNamespace(value="", update=lambda: None),
        page=SimpleNamespace(update=lambda: None),
        dpd_fields=fake_fields,
    )
    ctrl.word_in_text = "narena"
    ctrl.sentence_data = {**AI_DATA, **SOURCE_TEXT_DATA, "unknown_key": "x"}
    ctrl.load_into_gui()
    return fake_fields


def test_ai_keys_go_to_add_fields_only(dpd_fields: FakeDpdFields) -> None:
    for name in AI_DATA:
        assert dpd_fields.fields[name].value is None
    assert len(dpd_fields.add_calls) == 1
    offered = dpd_fields.add_calls[0]
    for name, value in AI_DATA.items():
        assert offered[name] == value
    for name in SOURCE_TEXT_DATA:
        assert name not in offered


def test_source_text_keys_fill_main_fields(dpd_fields: FakeDpdFields) -> None:
    for name, value in SOURCE_TEXT_DATA.items():
        assert dpd_fields.fields[name].value == value
