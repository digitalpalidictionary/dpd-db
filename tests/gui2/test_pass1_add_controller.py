"""Pass1Add must offer AI output as `_add` suggestions, never fill the fields."""

from types import SimpleNamespace
from unittest.mock import MagicMock

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


def test_load_into_gui_survives_missing_clipboard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A headless server has no clipboard; the word must still load."""

    def no_clipboard(_: str) -> None:
        raise controller_module.pyperclip.PyperclipException("no mechanism")

    monkeypatch.setattr(controller_module, "open_in_goldendict", lambda _: None)
    monkeypatch.setattr(controller_module.pyperclip, "copy", no_clipboard)

    fake_fields = FakeDpdFields()
    ctrl = object.__new__(Pass1AddController)
    ctrl.ui = SimpleNamespace(  # pyright: ignore[reportAttributeAccessIssue]
        word_in_text=SimpleNamespace(value="", update=lambda: None),
        page=SimpleNamespace(update=lambda: None),
        dpd_fields=fake_fields,
    )
    ctrl.word_in_text = "narena"
    ctrl.sentence_data = {**AI_DATA, **SOURCE_TEXT_DATA}
    ctrl.load_into_gui()

    assert ctrl.ui.word_in_text.value == "narena"
    assert len(fake_fields.add_calls) == 1


class _NoWordFinderToolkit:
    """A toolkit whose word finder raises: the controller must never touch it."""

    def __init__(self) -> None:
        self.db_manager: MagicMock = MagicMock()
        self.daily_log: MagicMock = MagicMock()
        self.paths: MagicMock = MagicMock()
        self.additions_manager: MagicMock = MagicMock()
        self.username_manager: MagicMock = MagicMock()

    @property
    def wordfinder_manager(self) -> MagicMock:
        raise AssertionError("Pass1AddController must not touch the word finder")


def test_controller_builds_without_touching_the_word_finder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(controller_module, "VariantReadingFileManager", MagicMock())
    monkeypatch.setattr(controller_module, "SpellingMistakesFileManager", MagicMock())

    ctrl = Pass1AddController(
        ui=MagicMock(),
        toolkit=_NoWordFinderToolkit(),  # pyright: ignore[reportArgumentType]
        pass1_auto_controller=MagicMock(),
    )

    assert ctrl.toolkit.db_manager is not None
    assert not hasattr(ctrl, "wordfinder_manager")


# --- saving a word typed in by hand must not cost the editor a book word ---


def _save_ctrl(
    monkeypatch: pytest.MonkeyPatch, box_value: str
) -> tuple[Pass1AddController, list[str], list[str]]:
    monkeypatch.setattr(controller_module, "save_headword", lambda *a: (True, ""))
    removed: list[str] = []
    loaded: list[str] = []
    ctrl = object.__new__(Pass1AddController)
    ctrl.daily_log = MagicMock()
    ctrl.toolkit = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    ctrl.db = MagicMock()
    ctrl.book_to_process = "book"
    ctrl.pass1_auto_controller = MagicMock()
    ctrl.pass1_auto_controller.remove_word.side_effect = lambda _b, w: removed.append(w)
    ctrl.pass1_auto_controller.get_auto_processed_dict.return_value = {}
    ctrl.auto_processed_iter = iter([("b", {"pos": "x"})])
    ctrl.word_in_text = "a"
    ctrl.sentence_data = {"pos": "x"}
    ctrl.load_into_gui = lambda: loaded.append(ctrl.word_in_text)  # pyright: ignore[reportAttributeAccessIssue]
    ctrl.ui = MagicMock()
    ctrl.ui.word_in_text.value = box_value
    return ctrl, removed, loaded


def test_saving_a_hand_typed_word_keeps_the_book_word(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctrl, removed, loaded = _save_ctrl(monkeypatch, box_value="")
    ctrl._save_previewed_word(MagicMock(id=1, lemma_1="zzz"), "", False)

    assert removed == []
    assert loaded == ["a"]


def test_saving_the_book_word_moves_to_the_next_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctrl, removed, loaded = _save_ctrl(monkeypatch, box_value="a")
    ctrl._save_previewed_word(MagicMock(id=1, lemma_1="a"), "", False)

    assert removed == ["a"]
    assert loaded == ["b"]


def test_hand_typed_save_after_the_last_book_word_loads_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctrl, _, loaded = _save_ctrl(monkeypatch, box_value="a")
    ctrl.auto_processed_iter = iter([])
    ctrl._save_previewed_word(MagicMock(id=1, lemma_1="a"), "", False)
    ctrl.ui.word_in_text.value = ""
    ctrl._save_previewed_word(MagicMock(id=2, lemma_1="zzz"), "", False)

    assert loaded == []
