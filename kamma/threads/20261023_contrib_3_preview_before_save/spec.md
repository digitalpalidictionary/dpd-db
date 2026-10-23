# Spec: preview before save — the webapp view of the unsaved word

**Thread:** 20261023_contrib_3_preview_before_save
**Date:** 2026-10-07
**GitHub issue:** [#215 — Contributor Onboarding](https://github.com/digitalpalidictionary/dpd-db/issues/215)
(commits reference `#215`)
**Depends on:** `20261023_contrib_2_edits_json` — must be finished first. It
adds the save seam (`gui2/save_router.py::save_headword`) that the Save button
here calls, and it edits the same two save handlers. Never run both threads in
the same working tree at once.
**Sibling:** `20261023_contrib_4_temp_server_test` (its live checks include this preview).

## Overview

After a save, gui2 opens the finished word in a browser via the local webapp
(`tools/fast_api_utils.py::request_dpd_server`, called at
`gui2/pass1_add_controller.py:182` and `gui2/pass2_add_view.py:863`). On the
server this would open on the server machine, so 20260719 switched it off there
(`tools/server_mode.py`). Contributors get no view of the finished word.

New behaviour, for everyone including user 1: the save button shows the word
as the webapp would show it, rendered from the UNSAVED word, in a browser tab
on the user's own machine. A dialog in gui2 then offers **Save** or **Cancel**.
The form stays filled until Save.

## Decisions made (2026-10-07, do not relitigate)

- 1A: The preview is the real webapp headword HTML, rendered from the unsaved
  word, opened in a browser tab. Save / Cancel buttons are in gui2.
- 2A: Everyone gets the preview step, user 1 included. This is the one
  workflow change for user 1: one extra click per save, and the browser tab
  opens BEFORE the save, from the unsaved word.
- The re-edit button is labelled "Cancel", so the global Escape handler
  (`gui2/ui_utils.py::cancel_top_dialog`, which presses a button whose label is
  in `_CANCEL_LABELS`) covers it.

## Current behaviour / facts (verified 2026-10-07)

### Webapp rendering
- `exporter/webapp/toolkit.py::make_dpd_html` renders one word as
  `HeadwordData(i, fc, fi, fs)` (`exporter/webapp/data_classes.py`) + the
  Jinja template `dpd_headword.html` in `exporter/webapp/templates/`
  (`ProjectPaths.webapp_templates_dir`, `template_dpd_headword`).
- The template reads `d.i.rt`, `d.i.fr`, `d.i.fw` (relationships) and `d.su`.
  It also reads plain columns and `@cached_property` helpers
  (`needs_*_button`, `meaning_combo_html`, `degree_of_completion_html`, ...).
- `DpdHeadword.su` (`db/models.py`) needs `object_session(self)` and returns
  None without one. `get_family_compounds/idioms/set`
  (`tools/exporter_functions.py`) raise "No db_session" without one.
- `HeadwordData.convert_newlines` MUTATES the object passed in (replaces `\n`
  with `<br>` on 9 string columns). So it must get a copy.
- Checked helpers that do not touch the session: `needs_sutta_info_button`
  (cache_load set), `needs_root_family_button` (plain column). Not every helper
  was read.
- Styles/scripts: `exporter/webapp/static/dpd.css`, `dpd.js`
  (`ProjectPaths.webapp_static_dir`).
- `exporter/webapp/main.py` builds the FastAPI app and loads data at import. Do
  NOT import it from gui2. Import `data_classes` and build a Jinja
  `Environment` directly.

### Flet facts
- `ft.WebView` supports iOS, Android, macOS and web only, not Linux desktop,
  and `flet_webview` is not installed. So an in-app page is not possible for
  user 1 (Linux Mint).
- Flet 1.0 `UrlLauncher.launch_url` (`flet/controls/services/url_launcher.py`)
  runs on the client. Desktop opens the system browser; web opens a tab in the
  user's own browser.
- Flet web serves `assets_dir` as static files. `ft.run` defaults it to
  `"assets"`, resolved against the working directory; `flet run` has
  `-a ASSETS_DIR`. Neither `assets/` nor `gui2/assets/` exists today.
- gui2 is started as `ft.run(main)` (`gui2/main.py`) on desktop and as
  `uv run flet run --web -p <port> gui2/main.py` on a server.

### Save handlers (after thread 1)
- Pass1Add: `make_dpd_headword_and_add_to_db` — checks (db loaded, spelling,
  duplicates), then the seam, then history, daily log, clear, and load next.
- Pass2Add: `_click_add_to_db` — checks (db loaded, spelling, duplicates for
  new words), then the seam, then the post-save steps.
- The webapp server (`start_dpd_server`) has other uses on desktop (lookups)
  and stays.

## What it should do

1. `render_preview(db_session, word) -> str` renders `dpd_headword.html` with
   the webapp's `HeadwordData` from a COPY of the unsaved word. `rt`, `fr`,
   `fw`, `su` and the family lists (`fc`, `fi`, `fs`) are looked up read-only
   from the db using the copy's key fields. The live word and every db row
   stay unchanged, and nothing is committed.
2. The result is wrapped in a minimal HTML page with `dpd.css` and `dpd.js`
   inlined. It is written to `gui2/assets/preview/preview_{username}.html`
   (gitignored).
3. Desktop opens `file://<abs path>`. Web opens a URL relative to the page
   (`preview/preview_{u}.html?t=<timestamp>`), so it works behind an nginx
   path prefix.
4. The Pass1Add and Pass2Add save buttons run the existing checks first. Then
   they render and open the preview and show a modal dialog:
   - **Save** → the seam + the post-save steps that follow it today, including
     clearing / loading the next item in Pass1Add.
   - **Cancel** / Escape → close the dialog. The form is untouched.
   - **Open preview** link button (`url=` property, a direct user click), as a
     fallback if the browser blocked the automatic tab.
5. The two `request_dpd_server` calls after save are removed.

## Assumptions & uncertainties

- **Popup blocking (unverified).** `launch_url` in web mode fires after a
  websocket round trip, not inside the click gesture, so Chrome may block the
  tab. The "Open preview" link is the decided fallback. Check live.
- **Asset serving (unverified).** Which `assets_dir` `flet run --web` uses,
  and whether a file written after start-up is served, must be checked live.
  Set `assets_dir` explicitly if needed.
- **Path prefix behind nginx**: only checkable on a server
  (`20261023_contrib_4_temp_server_test`, optional step). Locally, check that the URL is
  relative.
- **Template coverage with a transient word**: the executor renders real words
  of several kinds and a sample of random words to catch helpers that need a
  session.
- **Build-time fields are stale in the preview** (inflections_html, freq_html,
  family htmls). That is the same as today's after-save webapp view, because
  only the db build refreshes them.

## Constraints

- User 1: identical behaviour except the preview dialog before each save.
- Never mutate a session-attached ORM object. The preview works on a
  transient copy that is never added to a session.
- Flet 1.0 dialogs: closing with `open = False` leaves the instance on
  `page._dialogs`, and reopening the same instance raises "Dialog is already
  opened". Guard the reopen (see `CLAUDE.md`, Docs Lookups).
- Project rules: ruff check --fix, ruff format, pyright
  (`--project /dev/null` for gui2/tests files) and related pytest on every
  touched file. `just typecheck` at the end.
- No git commands. The user commits. Phase checkpoints are report-only.

## How we'll know it's done

1. Unit tests: `render_preview` gives HTML for an unsaved new word and for an
   edited copy of an existing word (with a root, a compound family and sutta
   info). The HTML holds the edited meaning, the db row is unchanged, and the
   session has nothing dirty or new. 20 random real words render with no
   exception.
2. Live desktop run as user 1: Pass1Add and Pass2Add → Chrome shows the
   preview → Cancel and Escape keep the form → Save writes the db, and Pass1Add
   loads the next item. Opening the dialog twice gives no red screen.
3. Live local web run as a contributor: the preview opens in the browser tab
   (or via the link if blocked). Save writes the JSON.
4. Full pytest suite and `just typecheck` pass.

## What's not included

- An in-app (WebView) preview.
- Regenerating build-time fields (inflections, frequency) for the preview.
- Server work (`20261023_contrib_4_temp_server_test`).
