"""render_preview builds the webapp page of an unsaved word from a copy."""

import asyncio
import random
from pathlib import Path
from types import SimpleNamespace

import pytest

from db.db_helpers import get_db_session
from db.models import DpdHeadword
import gui2.pass1_add_controller as controller_module
import gui2.preview as preview_module
from gui2.dpd_fields_functions import make_dpd_headword_from_dict
from gui2.pass1_add_controller import Pass1AddController
from gui2.preview import preview_url, render_preview, write_preview

MARKER = "zzpreviewmarkerzz"
# 8 has a root and a root family, 7 has a compound family, 7281 has sutta info
WORD_IDS = (8, 7, 7281)


@pytest.fixture(scope="module")
def db_session():
    session = get_db_session(Path("dpd.db"))
    yield session
    session.close()


def edited_copy(session, word_id: int) -> tuple[DpdHeadword, str]:
    row = session.get(DpdHeadword, word_id)
    assert row is not None
    values = {
        column.name: str(getattr(row, column.name) or "")
        for column in DpdHeadword.__table__.columns
    }
    values["meaning_1"] = MARKER
    return make_dpd_headword_from_dict(values), row.meaning_1


@pytest.mark.parametrize("word_id", WORD_IDS)
def test_edited_word_renders_with_the_new_meaning(db_session, word_id):
    word, original_meaning = edited_copy(db_session, word_id)
    html = render_preview(db_session, word)
    assert MARKER in html
    assert "<style>" in html and "<script>" in html
    assert db_session.get(DpdHeadword, word_id).meaning_1 == original_meaning
    assert not db_session.dirty
    assert not db_session.new


def test_root_family_and_sutta_info_reach_the_page(db_session):
    root_word, _ = edited_copy(db_session, 8)
    assert "kaṅkh" in render_preview(db_session, root_word)
    sutta_word, _ = edited_copy(db_session, 7281)
    assert "sutta-info-button" in render_preview(db_session, sutta_word)


def test_new_word_renders(db_session):
    word = make_dpd_headword_from_dict(
        {"lemma_1": "zzzword 1", "pos": "masc", "meaning_1": MARKER}
    )
    assert MARKER in render_preview(db_session, word)
    assert not db_session.new


def test_random_real_words_render(db_session):
    ids = [row[0] for row in db_session.query(DpdHeadword.id).all()]
    for word_id in random.Random(1).sample(ids, 20):
        word, _ = edited_copy(db_session, word_id)
        assert render_preview(db_session, word)


def test_write_preview_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = write_preview("<html></html>", "alice")
    assert path.name == "preview_alice.html"
    assert path.read_text(encoding="utf-8") == "<html></html>"


def test_preview_url_shapes(tmp_path):
    path = tmp_path / "preview_alice.html"
    assert preview_url(path, is_web=False) == path.resolve().as_uri()
    web = preview_url(path, is_web=True)
    assert web.startswith("preview/preview_alice.html?t=")


def test_page_is_dark_opens_grammar_and_hides_audio(db_session):
    word, _ = edited_copy(db_session, 8)
    html = render_preview(db_session, word)
    assert 'class="dark-mode"' in html
    assert 'a[name="grammar-button"]' in html
    assert ".dpd-button.play{display:none}" in html


def test_body_is_a_normal_scrolling_page(db_session):
    word, _ = edited_copy(db_session, 8)
    html = render_preview(db_session, word)
    assert html.rindex("body{height:auto") > html.rindex("body {")


# --- dialog flow: a fake page, so no Flet client is needed ---


class FakePage:
    web = False

    def __init__(self) -> None:
        self.dialogs: list = []

    def show_dialog(self, dialog) -> None:
        self.dialogs.append(dialog)

    def update(self) -> None:
        pass


def button(dialog, label: str):
    return next(a for a in dialog.actions if a.content == label)


@pytest.fixture
def flow(monkeypatch):
    """preview_and_confirm with the render, write and open steps faked."""
    monkeypatch.setattr(preview_module, "_in_progress", False)
    monkeypatch.setattr(preview_module, "render_preview", lambda *_: "<html>")
    monkeypatch.setattr(preview_module, "write_preview", lambda *_: Path("p.html"))

    async def fake_open(page, path) -> str:
        return "file:///p.html"

    monkeypatch.setattr(preview_module, "open_preview", fake_open)
    saves: list[int] = []

    async def on_save() -> None:
        saves.append(1)

    page = FakePage()

    def start() -> None:
        asyncio.run(
            preview_module.preview_and_confirm(page, None, None, "alice", on_save)  # pyright: ignore[reportArgumentType]
        )

    return SimpleNamespace(page=page, saves=saves, start=start)


def test_nothing_saves_before_save_is_pressed(flow):
    flow.start()
    assert len(flow.page.dialogs) == 1
    assert flow.saves == []


def test_save_runs_once_even_when_pressed_twice(flow):
    flow.start()
    save = button(flow.page.dialogs[0], "Save")
    asyncio.run(save.on_click(None))
    asyncio.run(save.on_click(None))
    assert flow.saves == [1]


@pytest.mark.parametrize("event", [None, object()])
def test_cancel_and_escape_save_nothing_and_free_the_next_preview(flow, event):
    flow.start()
    button(flow.page.dialogs[0], "Cancel").on_click(event)
    assert flow.saves == []
    flow.start()
    assert len(flow.page.dialogs) == 2


def test_second_preview_while_one_is_open_is_ignored(flow):
    flow.start()
    flow.start()
    assert len(flow.page.dialogs) == 1


def test_failed_render_still_offers_save(flow, monkeypatch):
    def broken(*_):
        raise ValueError("bad word")

    monkeypatch.setattr(preview_module, "render_preview", broken)
    flow.start()
    dialog = flow.page.dialogs[0]
    assert "bad word" in dialog.content.value
    assert all(a.content != "Open preview" for a in dialog.actions)
    asyncio.run(button(dialog, "Save").on_click(None))
    assert flow.saves == [1]


def test_username_cannot_leave_the_preview_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = write_preview("<html></html>", "../evil")
    assert path.parent == preview_module.PREVIEW_DIR
    assert "/" not in path.name


# --- the two save handlers only save from the dialog ---


def test_pass1_save_button_saves_nothing_until_the_dialog(monkeypatch):
    saved: list[int] = []
    monkeypatch.setattr(
        controller_module, "save_headword", lambda *a: saved.append(1) or (True, "")
    )
    scheduled: list = []
    field = lambda value: SimpleNamespace(value=value)  # noqa: E731
    ctrl = object.__new__(Pass1AddController)
    ctrl.db = SimpleNamespace(  # pyright: ignore[reportAttributeAccessIssue]
        is_db_loaded=lambda: True, get_next_id=lambda: 5
    )
    ctrl.ui = SimpleNamespace(  # pyright: ignore[reportAttributeAccessIssue]
        update_message=lambda _: None,
        page=SimpleNamespace(run_task=lambda *a: scheduled.append(a)),
        dpd_fields=SimpleNamespace(
            fields={"lemma_1": field("zzz 1"), "meaning_2": field("")},
            get_field=lambda _: field(""),
            spellchecker=SimpleNamespace(check_sentence=lambda _: {}),
            validate_no_duplicates=lambda *_: True,
        ),
    )
    ctrl.make_dpd_headword_and_add_to_db()
    assert len(scheduled) == 1
    assert saved == []
