"""render_preview builds the webapp page of an unsaved word from a copy."""

import asyncio
import base64
import json
import random
import re
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from audio.db.db_helpers import get_audio_record
from db.db_helpers import get_db_session
from db.models import DpdHeadword
import gui2.pass1_add_controller as controller_module
import gui2.preview as preview_module
from gui2.dpd_fields_functions import make_dpd_headword_from_dict
from gui2.pass1_add_controller import Pass1AddController
from gui2.preview import preview_url, render_preview, write_preview
from tools.paths import ProjectPaths

MARKER = "zzpreviewmarkerzz"
# 8 has a root and a root family, 7 has a compound family, 7281 has sutta info
WORD_IDS = (8, 7, 7281)


@pytest.fixture(scope="module")
def db_session():
    session = get_db_session(Path("dpd.db"))
    yield session
    session.close()


@pytest.fixture(autouse=True, scope="module")
def load_word_lists_once():
    """Each preview reads about 50 MB of word lists. The tests share one read."""
    real = preview_module.make_all_tipitaka_word_set
    try:
        words = real()
    except FileNotFoundError:
        # generated files: the preview itself copes without them
        yield
        return
    preview_module.make_all_tipitaka_word_set = lambda: words
    yield
    preview_module.make_all_tipitaka_word_set = real


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


def test_new_word_gets_an_inflection_table(db_session):
    word = make_dpd_headword_from_dict(
        {
            "lemma_1": "zzzword 1",
            "pos": "masc",
            "meaning_1": MARKER,
            "stem": "zzzword",
            "pattern": "a masc",
        }
    )
    html = render_preview(db_session, word)
    assert "<table class='inflection'>" in html
    assert "is <b>a masc</b> declension" in html
    assert "zzzword<b>assa</b>" in html
    assert not db_session.new


def test_changed_pattern_replaces_the_stored_table(db_session):
    word, _ = edited_copy(db_session, 7)
    assert "is <b>a adj</b>" in word.inflections_html
    word.pattern = "a nt"
    html = render_preview(db_session, word)
    assert "is <b>a nt</b>" in html
    assert "is <b>a adj</b>" not in html


def test_new_word_frequency_says_not_yet_built(db_session):
    word = make_dpd_headword_from_dict(
        {"lemma_1": "zzzword 1", "pos": "masc", "meaning_1": MARKER}
    )
    html = render_preview(db_session, word)
    assert "Not yet built" in html
    assert "There are no matches" not in html


def test_existing_word_without_matches_keeps_the_webapp_text(db_session):
    # word 108 is saved with an empty freq_html: it was counted and has no matches
    word, _ = edited_copy(db_session, 108)
    assert not word.freq_html
    html = render_preview(db_session, word)
    assert "There are no matches" in html
    assert "Not yet built" not in html


def test_stored_frequency_is_kept(db_session):
    word, _ = edited_copy(db_session, 7)
    assert word.freq_html
    html = render_preview(db_session, word)
    assert "Not yet built" not in html
    assert word.freq_html in html


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


def test_page_is_dark_and_opens_grammar(db_session):
    word, _ = edited_copy(db_session, 8)
    html = render_preview(db_session, word)
    assert 'class="dark-mode"' in html
    assert 'a[name="grammar-button"]' in html


# --- audio: word 7 (akakkasa) has all three voices in the audio index ---

HIDE_PLAY = ".dpd-button.play{display:none}"
needs_audio_db = pytest.mark.skipif(
    not (
        ProjectPaths().dpd_audio_db_path.exists()
        and ProjectPaths().dpd_audio_index_tsv_path.exists()
    ),
    reason="audio db and index not downloaded",
)
NO_AUDIO_WORD = {"lemma_1": "zzzword 1", "pos": "masc", "meaning_1": MARKER}


@needs_audio_db
def test_word_with_audio_embeds_it_and_shows_the_button(db_session):
    word, _ = edited_copy(db_session, 7)
    html = render_preview(db_session, word)
    assert html.count("data:audio/mpeg;base64,") == 3
    assert HIDE_PLAY not in html


def test_word_without_audio_keeps_the_button_hidden(db_session):
    html = render_preview(db_session, make_dpd_headword_from_dict(NO_AUDIO_WORD))
    assert HIDE_PLAY in html
    assert "data:audio" not in html


def test_missing_audio_db_is_skipped_without_creating_it(
    db_session, monkeypatch, tmp_path
):
    missing = tmp_path / "dpd_audio.db"
    calls: list[str] = []

    class PathsWithoutAudioDb(ProjectPaths):
        def __init__(self) -> None:
            super().__init__()
            self.dpd_audio_db_path = missing

    monkeypatch.setattr(preview_module, "ProjectPaths", PathsWithoutAudioDb)
    monkeypatch.setattr(
        preview_module, "get_audio_record", lambda *args: calls.append(args[0])
    )
    word, _ = edited_copy(db_session, 7)
    html = render_preview(db_session, word)
    assert MARKER in html
    assert HIDE_PLAY in html
    assert calls == []
    assert not missing.exists()


def test_missing_audio_index_leaves_the_preview_working(db_session, monkeypatch):
    def no_index() -> dict:
        raise FileNotFoundError("no audio index")

    monkeypatch.setattr(preview_module, "load_audio_dict", no_index)
    word, _ = edited_copy(db_session, 7)
    html = render_preview(db_session, word)
    assert MARKER in html
    assert HIDE_PLAY in html


@needs_audio_db
@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_audio_script_answers_the_webapp_audio_urls(db_session):
    word, _ = edited_copy(db_session, 7)
    html = render_preview(db_session, word)
    script = re.search(r'<script id="preview-audio">(.*?)</script>', html, re.S)
    assert script
    harness = (
        "globalThis.window = {};"
        "window.Audio = class { constructor(url) { this.url = url; } };"
        + script.group(1)
        + "const urls = ['male', 'female', 'male1', 'male2', 'female1', 'bogus']"
        ".map(g => new window.Audio("
        "'/audio/' + encodeURIComponent('akakkasa 1') + '?gender=' + g).url);"
        "urls.push(new window.Audio('/audio/other?gender=male').url);"
        "console.log(JSON.stringify(urls));"
    )
    out = subprocess.run(
        ["node", "-e", harness], capture_output=True, text=True, check=True
    )
    male, female, male1, male2, female1, bogus, other = json.loads(out.stdout)

    def recording(gender: str) -> str:
        data = get_audio_record("akakkasa", gender)
        assert data
        return "data:audio/mpeg;base64," + base64.b64encode(data).decode("ascii")

    assert male1 == recording("male1")
    assert male2 == recording("male2")
    assert female1 == recording("female1")
    assert male == bogus == recording("male1")
    assert female == recording("female1")
    assert male1 != male2 and male1 != female1
    assert other == "/audio/other?gender=male"


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
    monkeypatch.setattr(preview_module, "_owner", None)
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

    return SimpleNamespace(page=page, saves=saves, start=start, on_save=on_save)


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


def test_a_new_page_can_preview_while_an_old_page_left_its_dialog_open(flow):
    flow.start()
    other = FakePage()
    asyncio.run(
        preview_module.preview_and_confirm(
            other,  # pyright: ignore[reportArgumentType]
            None,  # pyright: ignore[reportArgumentType]
            None,  # pyright: ignore[reportArgumentType]
            "alice",
            flow.on_save,
        )
    )
    assert len(other.dialogs) == 1


def test_save_on_a_retired_page_saves_nothing(flow):
    flow.start()
    preview_module.retire_page(flow.page)
    save = button(flow.page.dialogs[0], "Save")
    asyncio.run(save.on_click(None))
    assert flow.saves == []


def test_save_on_the_old_page_saves_nothing_after_a_new_page_took_the_preview(flow):
    flow.start()
    other = FakePage()
    asyncio.run(
        preview_module.preview_and_confirm(
            other,  # pyright: ignore[reportArgumentType]
            None,  # pyright: ignore[reportArgumentType]
            None,  # pyright: ignore[reportArgumentType]
            "alice",
            flow.on_save,
        )
    )
    save = button(flow.page.dialogs[0], "Save")
    asyncio.run(save.on_click(None))
    assert flow.saves == []
    other_save = button(other.dialogs[0], "Save")
    asyncio.run(other_save.on_click(None))
    assert flow.saves == [1]


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
