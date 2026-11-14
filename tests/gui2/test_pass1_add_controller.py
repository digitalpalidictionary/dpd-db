"""Pass1Add must offer AI output as `_add` suggestions, never fill the fields."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest

import gui2.pass1_add_controller as controller_module
from gui2.pass1_add_controller import Pass1AddController
from gui2.pass1_file_manager import Pass1FileManager
from gui2.paths import Gui2Paths

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


# --- a word another contributor finished since the book opened is skipped ---


def _next_ctrl(
    words: list[str], finished: set[str]
) -> tuple[Pass1AddController, MagicMock]:
    ctrl = object.__new__(Pass1AddController)
    ctrl.book_to_process = "book"
    ctrl.pass1_auto_controller = MagicMock()
    ctrl.pass1_auto_controller.file_manager.finished_words.return_value = finished
    ctrl.pass1_auto_controller.get_auto_processed_dict.return_value = {
        word: {"pos": "x"} for word in words
    }
    ctrl.auto_processed_iter = iter([(word, {"pos": "x"}) for word in words])
    ctrl.ui = MagicMock()
    return ctrl, ctrl.ui


def test_next_item_skips_words_finished_by_others() -> None:
    ctrl, _ = _next_ctrl(["a", "b", "c"], finished={"b"})

    assert ctrl.get_next_item() is True
    assert ctrl.word_in_text == "a"
    assert ctrl.get_next_item() is True
    assert ctrl.word_in_text == "c"


def test_next_item_ends_when_every_word_was_finished_by_others() -> None:
    ctrl, ui = _next_ctrl(["a", "b"], finished={"a", "b"})

    assert ctrl.get_next_item() is False
    ui.update_message.assert_called_with("No more words to process.")
    ui.update_remaining.assert_called_with(0)


def test_remaining_count_leaves_out_words_finished_by_others() -> None:
    ctrl, ui = _next_ctrl(["a", "b", "c"], finished={"b"})

    ctrl.get_next_item()

    ui.update_remaining.assert_called_with(2)


def test_a_word_another_contributor_finishes_after_the_book_opened_is_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DPD_GUI2_DATA_DIR", str(tmp_path / "server_data"))

    def manager(user: str) -> Pass1FileManager:
        paths = Gui2Paths.for_user(user, base_dir=tmp_path)
        paths.gui2_data_path.mkdir(parents=True, exist_ok=True)
        return Pass1FileManager(paths)

    alice, bob = manager("alice"), manager("bob")
    (alice.gui2_data_path / "pass1_auto_vv.json").write_text(
        json.dumps({word: {"pos": "x"} for word in ("a", "b", "c")}), encoding="utf-8"
    )
    auto = MagicMock()
    auto.file_manager = alice
    auto.get_auto_processed_dict.side_effect = alice.read
    ctrl = object.__new__(Pass1AddController)
    ctrl.book_to_process = "vv"
    ctrl.pass1_auto_controller = auto
    ctrl.ui = MagicMock()
    # alice opens the book: the queue is copied once, as process_book does
    ctrl.auto_processed_iter = iter(dict(alice.read("vv")).items())

    bob.remove("vv", "b")

    assert ctrl.get_next_item() is True
    assert ctrl.word_in_text == "a"
    assert ctrl.get_next_item() is True
    assert ctrl.word_in_text == "c"
    assert ctrl.get_next_item() is False


def test_a_committed_new_word_notes_the_lemma_without_a_full_reread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctrl, _, _ = _save_ctrl(monkeypatch, box_value="")

    ctrl._save_previewed_word(MagicMock(id=1, lemma_1="zzz 1"), "", False)

    db = cast(MagicMock, ctrl.db)
    db.note_new_lemma.assert_called_once_with("zzz 1")
    db.get_all_lemma_1_and_lemma_clean.assert_not_called()


def test_a_committed_edit_still_rereads_the_lemmas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctrl, _, _ = _save_ctrl(monkeypatch, box_value="")

    ctrl._save_previewed_word(MagicMock(id=1, lemma_1="zzz 1"), "", True)

    db = cast(MagicMock, ctrl.db)
    db.get_all_lemma_1_and_lemma_clean.assert_called_once_with()
    db.note_new_lemma.assert_not_called()
