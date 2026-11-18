# -*- coding: utf-8 -*-
"""Preview a word as the webapp shows it, before it is saved.

The word is rendered from a transient copy: nothing is added to a session
and nothing is committed."""

import base64
import json
import re
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import flet as ft
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from audio.db.db_helpers import get_audio_record
from db.inflections.generate_inflection_tables import make_inflection_table
from db.models import (
    DpdHeadword,
    DpdRoot,
    FamilyCompound,
    FamilyIdiom,
    FamilyRoot,
    FamilySet,
    FamilyWord,
    InflectionTemplates,
    SuttaInfo,
    _load_sutta_alias_map,
)
from exporter.webapp.data_classes import HeadwordData
from tools.all_tipitaka_words import make_all_tipitaka_word_set
from tools.cache_load import load_audio_dict
from tools.configger import config_test
from tools.paths import ProjectPaths

PREVIEW_DIR = Path("gui2/assets/preview")

# The counts come from the Go frequency tool, which runs in the db build. The
# webapp's own text for an empty box ("no matches") would be false here.
FREQUENCY_NOT_BUILT = (
    "<br>Not yet built. The frequency is worked out when the dictionary is built."
)


class _WordWithRelations:
    """Gives the webapp template the db relationships of a transient word.
    Every other attribute comes from the copy. A write lands on the proxy, so
    the copy keeps its values."""

    def __init__(
        self,
        word: DpdHeadword,
        rt: DpdRoot | None,
        fr: FamilyRoot | None,
        fw: FamilyWord | None,
        su: SuttaInfo | None,
    ) -> None:
        self._word = word
        self.rt = rt
        self.fr = fr
        self.fw = fw
        self.su = su

    def __getattr__(self, name: str) -> Any:
        return getattr(self._word, name)


def _copy_of(word: DpdHeadword) -> DpdHeadword:
    copy = DpdHeadword()
    supplied = vars(word)
    for column in DpdHeadword.__table__.columns:
        if column.name in supplied:
            setattr(copy, column.name, supplied[column.name])
        elif column.default is not None and column.default.is_scalar:
            # a column default applies only on insert; the template needs it now
            setattr(copy, column.name, column.default.arg)
    return copy


def _ordered[T](rows: list[T], names: list[str], key: Callable[[T], str]) -> list[T]:
    return sorted(rows, key=lambda row: names.index(key(row)))


def _family_lists(
    db_session: Session, word: DpdHeadword
) -> tuple[list[FamilyCompound], list[FamilyIdiom], list[FamilySet]]:
    """The same lookups and order as tools/exporter_functions.py."""
    compound_names = word.family_compound_list or [word.lemma_clean]
    fc = (
        db_session.query(FamilyCompound)
        .filter(FamilyCompound.compound_family.in_(compound_names))
        .all()
    )
    idiom_names = word.family_idioms_list or [word.lemma_clean]
    fi = db_session.query(FamilyIdiom).filter(FamilyIdiom.idiom.in_(idiom_names)).all()
    fs = (
        db_session.query(FamilySet)
        .filter(FamilySet.set.in_(word.family_set_list))
        .all()
    )
    return (
        _ordered(fc, compound_names, lambda row: row.compound_family),
        _ordered(fi, idiom_names, lambda row: row.idiom),
        _ordered(fs, word.family_set_list, lambda row: row.set),
    )


def _inflection_table(db_session: Session, word: DpdHeadword) -> str:
    """The table the db build would write for this stem and pattern. Empty when
    the pattern has no template, as in the build."""
    template = db_session.get(InflectionTemplates, word.pattern)
    if template is None or not template.data:
        return ""
    try:
        # loaded per preview and dropped, so gui2 does not hold the set in memory
        tipitaka_words: set[str] | None = make_all_tipitaka_word_set()
    except FileNotFoundError:
        # generated files, absent on some machines: no cell is greyed out
        tipitaka_words = None
    return make_inflection_table(word, template, tipitaka_words)[0]


# dpd.js plays a word with `new Audio('/audio/<word>?gender=<g>')`, a url that only
# the webapp server answers. This swaps in the embedded recordings; the fallbacks
# are those of audio.db.db_helpers.get_audio_record.
_AUDIO_SHIM = """
(function () {
  var word = %(word)s, voices = %(voices)s, RealAudio = window.Audio;
  function pick(gender) {
    if (gender === "male1" || gender === "male2" || gender === "female1")
      return voices[gender];
    if (gender === "female") return voices.female1 || voices.male1;
    return voices.male1 || voices.female1;
  }
  window.Audio = function (url) {
    var match = /^\\/audio\\/([^?]*)\\?gender=(.*)$/.exec(url);
    if (match && decodeURIComponent(match[1]).replace(/ \\d.*$/, "") === word)
      url = pick(match[2]) || url;
    return new RealAudio(url);
  };
})();
"""


def _audio_script(word: DpdHeadword) -> str:
    """A script tag with the word's recordings embedded, or "" when there is
    nothing to play. Opening a missing sqlite file would create an empty one, so
    the file is checked first: the contributor server does not download it."""
    if not ProjectPaths().dpd_audio_db_path.exists():
        return ""
    try:
        availability = load_audio_dict().get(word.lemma_clean)
        if not availability:
            return ""
        voices = {
            gender: "data:audio/mpeg;base64,"
            + base64.b64encode(recording).decode("ascii")
            for gender, present in zip(("male1", "male2", "female1"), availability)
            if present and (recording := get_audio_record(word.lemma_clean, gender))
        }
    except (FileNotFoundError, OperationalError):
        # the index or the db is not downloaded on this machine
        return ""
    if not voices:
        return ""
    shim = _AUDIO_SHIM % {
        "word": json.dumps(word.lemma_clean),
        "voices": json.dumps(voices),
    }
    return f'<script id="preview-audio">{shim.replace("</", "<\\/")}</script>'


def render_preview(db_session: Session, word: DpdHeadword) -> str:
    """The webapp headword HTML of an unsaved word, wrapped in a page with the
    webapp's css and js inlined."""
    pth = ProjectPaths()
    copy = _copy_of(word)

    with db_session.no_autoflush:
        rt = db_session.get(DpdRoot, copy.root_key) if copy.root_key else None
        fr = (
            db_session.query(FamilyRoot)
            .filter(
                FamilyRoot.root_key == copy.root_key,
                FamilyRoot.root_family == copy.family_root,
            )
            .first()
            if copy.root_key and copy.family_root
            else None
        )
        fw = db_session.get(FamilyWord, copy.family_word) if copy.family_word else None
        canonical = _load_sutta_alias_map().get(copy.lemma_1)
        su = db_session.get(SuttaInfo, canonical) if canonical else None
        fc, fi, fs = _family_lists(db_session, copy)
        if copy.pattern:
            copy.inflections_html = _inflection_table(db_session, copy)
        # a saved word with no matches was counted: the webapp's own text is true for it
        if not copy.freq_html and (
            not copy.id or db_session.get(DpdHeadword, copy.id) is None
        ):
            copy.freq_html = FREQUENCY_NOT_BUILT

    d = HeadwordData(_WordWithRelations(copy, rt, fr, fw, su), fc, fi, fs)  # type: ignore[arg-type]

    env = Environment(
        loader=FileSystemLoader(str(pth.webapp_templates_dir)), autoescape=True
    )
    env.globals["show_tbw"] = config_test("dictionary", "show_tbw", "yes")
    body = env.get_template(pth.template_dpd_headword).render(d=d)

    # the same style files, in the same order, as the webapp's home page
    css = "".join(
        (pth.webapp_static_dir / name).read_text(encoding="utf-8")
        for name in ("dpd.css", "home.css", "switch.css", "tt.css")
    )
    js = (pth.webapp_static_dir / "dpd.js").read_text(encoding="utf-8")
    audio_script = _audio_script(copy)
    return (
        '<!DOCTYPE html><html lang="en" class="dark-mode"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Preview</title>"
        f"<style>{css}"
        # without embedded audio the play button would ask a server that is not there
        f"{'' if audio_script else '.dpd-button.play{display:none}'}"
        # home.css makes body a fixed-height flex column, which squeezes the
        # summary box when a long section opens
        "body{height:auto;overflow:auto;display:block;"
        "max-width:700px;margin:0 auto;padding:1em}</style>"
        f"<script>{js}</script>{audio_script}</head><body>{body}"
        "<script>document.querySelector('a[name=\"grammar-button\"]')?.click()</script>"
        "</body></html>"
    )


def write_preview(html: str, username: str) -> Path:
    """Write the page where the Flet assets server finds it."""
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w.-]", "_", username)
    path = PREVIEW_DIR / f"preview_{safe_name}.html"
    path.write_text(html, encoding="utf-8")
    return path


def preview_url(path: Path, is_web: bool) -> str:
    """Desktop opens the file itself. A web session opens a url relative to the
    page, so it works behind a path prefix; the timestamp skips the cache."""
    if is_web:
        return f"preview/{path.name}?t={int(time.time())}"
    return path.resolve().as_uri()


async def open_preview(page: ft.Page, path: Path) -> str:
    url = preview_url(path, bool(page.web))
    await ft.UrlLauncher().launch_url(url)
    return url


async def show_preview_dialog(
    page: ft.Page,
    url: str | None,
    on_save: Callable[[], Awaitable[None]],
    on_cancel: Callable[[], None],
    note: str = "",
) -> None:
    """A modal dialog: Save runs on_save, Cancel keeps the form as it is. The
    Open preview link is the fallback when the browser blocked the tab. With no
    url the preview failed, and note says why: the word can still be saved."""
    saved = False

    def close() -> None:
        dialog.open = False
        page.update()

    async def on_save_click(_: ft.Event[ft.Button]) -> None:
        nonlocal saved
        # a second click can arrive before the client has closed the dialog
        if saved:
            return
        saved = True
        close()
        await on_save()

    # Escape calls this with None, see ui_utils.cancel_top_dialog
    def on_cancel_click(_: ft.Event[ft.TextButton] | None) -> None:
        close()
        on_cancel()

    actions: list[ft.Control] = []
    if url:
        actions.append(ft.TextButton("Open preview", url=url))
    actions.append(ft.TextButton("Cancel", on_click=on_cancel_click))
    actions.append(ft.Button("Save", on_click=on_save_click))
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Preview before save"),
        content=ft.Text(note or "The preview opened in your browser."),
        actions=actions,
    )
    page.show_dialog(dialog)
    page.update()


# The page whose preview dialog is open. Held per page, not per process: a
# reload or a second tab makes a new page, and a process-wide flag left set
# by the old page's dialog would block every later save.
_owner: ft.Page | None = None


def retire_page(page: ft.Page) -> None:
    """Forget a page that a newer page replaced. Its dialog can no longer save."""
    global _owner
    if _owner is page:
        _owner = None


async def preview_and_confirm(
    page: ft.Page,
    db_session: Session,
    word: DpdHeadword,
    username: str,
    on_save: Callable[[], Awaitable[None]],
) -> None:
    """Open the preview in the browser, then ask: Save or Cancel. A second call
    from the same page while its preview is open or saving does nothing."""
    global _owner
    if _owner is page:
        return
    _owner = page

    def release() -> None:
        global _owner
        if _owner is page:
            _owner = None

    async def save() -> None:
        # A retired page holds a stale copy of the contributor's file; a save
        # from it would be overwritten by the live page's next save.
        if _owner is not page:
            return
        try:
            await on_save()
        finally:
            release()

    try:
        url: str | None = None
        note = ""
        try:
            path = write_preview(render_preview(db_session, word), username)
            url = await open_preview(page, path)
        except Exception as ex:  # noqa: BLE001
            # a broken preview must never block saving the word
            note = f"Preview failed: {ex!s}"
        await show_preview_dialog(page, url, save, release, note)
    except Exception:
        release()
        raise
