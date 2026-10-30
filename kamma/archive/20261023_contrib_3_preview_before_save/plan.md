# Plan: preview before save — the webapp view of the unsaved word

**Thread:** 20261023_contrib_3_preview_before_save · **Spec:** `spec.md` (read first)
**GitHub issue:** #215 — commits reference `#215`
**Start only after** `20261023_contrib_2_edits_json` AND
`20261030_contrib_5_hardening` are finished (needs
`gui2/save_router.py::save_headword`; contrib_5 also edits
`gui2/pass2_add_view.py` — Reject button, proposal fields).
**Note (2026-10-30, contrib_5):** contributors on the server never see Pass2Add
for now, and their per-user files live in `DPD_GUI2_DATA_DIR`. The contributor
check (2.2) uses Pass1Add only.

## Model Strategy

| Phase | Model | Why |
|---|---|---|
| 1 Render the preview | Sonnet | Follows the webapp's own render path, with tests |
| 2 Preview dialog | Sonnet | UI wiring plus live checks with the user |
| 3 Finish | Sonnet | Docs, typecheck, tests |

## Architecture Decisions
- **Real webapp template on a transient copy**, wrapped in a small proxy class
  that supplies `rt` / `fr` / `fw` / `su` from read-only queries and delegates
  every other attribute to the copy. Nothing is session-attached and nothing is
  committed.
- **New module `gui2/preview.py`** holds the render and write/open code, so it
  can be tested without Flet views.
- **Do not import `exporter/webapp/main.py`** (it builds the app and loads data
  at import). Use `exporter/webapp/data_classes.HeadwordData` + a Jinja
  `Environment` on `webapp_templates_dir`.
- **Browser tab, not an in-app page**: WebView does not run on Linux desktop.
- Not abstracted: no generic "render any webapp page" layer.

## Phase 1 — Render the preview — *Sonnet*
- [x] 1.1 `gui2/preview.py::render_preview(db_session, word) -> str`. Copy the
      word's column values into a new transient `DpdHeadword` (via
      `make_dpd_headword_from_dict`). Wrap it in a proxy with `rt` (DpdRoot by
      root_key), `fr` (FamilyRoot by root_key + family_root), `fw` (FamilyWord by
      family_word), `su` (SuttaInfo via the alias map, as `DpdHeadword.su` does).
      Query fc/fi/fs directly with the same filters and sort order as
      `tools/exporter_functions.py`. Build `HeadwordData(proxy, fc, fi, fs)` and
      render `dpd_headword.html`. Wrap it in a minimal HTML page with `dpd.css`
      and `dpd.js` inlined.
      → verify: `tests/gui2/test_preview.py` on the real `dpd.db`, read-only:
      render an unsaved new word and an edited copy of an existing word with a
      root, a compound family and sutta info. The HTML contains the edited
      meaning, the db row is unchanged, and `session.dirty` / `session.new` are
      empty afterwards. Then render 20 random real words with no exception. Mark
      the test `slow` if it takes over ~5 s.
- [x] 1.2 Write and open: `write_preview(html, username) -> Path` writes
      `gui2/assets/preview/preview_{username}.html` (add `gui2/assets/preview/` to
      `.gitignore`). `open_preview(page, path)`: desktop →
      `launch_url("file://<abs>")`; web (`page.web`) → relative
      `preview/preview_{u}.html?t=<ts>`. Make sure `ft.run` (desktop) and
      `flet run --web` serve `gui2/assets` (set `assets_dir` / `-a` if needed, and
      record which was needed here).
      → verify: unit test for the path and URL shapes. Then a live web run
      (`uv run flet run --web -p 8550 gui2/main.py`) WITH the user, calling the
      preview from a temporary debug trigger or straight from 2.1: the tab opens
      and shows the word with webapp styling. Record whether the browser blocked
      the tab.
- [x] 1.3 Phase gate: ruff check --fix, ruff format, pyright
      (`--project /dev/null` for gui2/tests files) on touched files + related tests.
      Report only, no commit.
      → verify: all clean. Paste the counts here.

## Phase 2 — Preview dialog in the save flows — *Sonnet*
- [x] 2.1 One shared dialog helper (in `gui2/preview.py`) taking an `on_save`
      callback: modal `AlertDialog` with "Save", "Cancel" and an "Open preview"
      link button (`url=` property). Guard the reopen per the Flet 1.0 note in
      `CLAUDE.md`. Pass1Add (`make_dpd_headword_and_add_to_db`) and Pass2Add
      (`_click_add_to_db`): run the existing checks, then render + open + show the
      dialog. Move the seam call and every step after it into `on_save`. Remove
      the `request_dpd_server` calls at `pass1_add_controller.py:182` and
      `pass2_add_view.py:863`, and their imports if they become unused.
      → verify: `uv run pytest tests/gui2/`. Live desktop run WITH the user:
      Pass1Add and Pass2Add → Chrome shows the preview → Cancel keeps the form →
      Escape does the same → Save writes the db and Pass1Add loads the next item →
      opening the dialog twice gives no red screen.
- [x] 2.2 Live local web run as a contributor WITH the user:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && DPD_GUI2_USERNAME=alice DPD_GUI2_ROLE=contributor-server DPD_GUI2_DATA_DIR=<scratchpad>/alice uv run flet run --web -p 8551 gui2/main.py`.
      In Pass1Add (contributors have no Pass2Add): the preview opens in the
      browser (or via the link) → Save writes `<scratchpad>/alice/additions_alice.json`
      only, and the db row count is unchanged. Remove the test entries after.
      → verify: results logged here, including the popup-block result.
- [x] 2.3 Phase gate as 1.3 + `uv run pytest tests/`. Report only, no commit.
      → verify: full suite passes. Paste the counts here.

## Phase 3 — Finish — *Sonnet*
- [x] 3.1 Update `gui2/README.md` (the preview step before save). Run
      `just typecheck`, full pytest and `graphify update .`.
      → verify: all pass. Paste the counts here.

## Progress notes (2026-10-30)
- 1.1 done: `gui2/preview.py` + `tests/gui2/test_preview.py` (8 pass). Unset
  columns of the copy get their column default, so a sparse new word renders.
- 1.2 code done, the live web run is still open. `flet run --web` resolves
  `assets` against the script dir (`gui2/assets`), so no `-a` flag is needed.
  `ft.run(main)` on desktop is unchanged: desktop opens `file://`, so it needs
  no assets dir. `gui2/assets/preview/` is in `.gitignore`.
- 1.3: ruff check/format clean on all touched files. `pyright --project /dev/null`:
  preview.py and test 0 errors; pass1_add_controller 3 (same as before);
  pass2_add_view 47 (was 50). No new errors.
- 2.1 code done, live runs open. Pass1Add schedules the preview with
  `page.run_task` (the button handler is sync). Both save handlers now keep
  their checks, then call `preview_and_confirm`; the seam call and the steps
  after it moved to `_save_previewed_word`. `request_dpd_server` calls and
  imports are removed from both files. `tests/gui2`: 592 pass.
- 2026-10-30 live desktop run, Pass1Add and Pass2Add: preview, Cancel, Escape
  and Save all work (user confirmed). Change requested: dark mode, done as
  spec decision 3A. Dark page confirmed. Next requests: grammar box open on load, play button hidden (no audio server in a preview): done.
- 2026-10-30 drift: `flet run` breaks the data paths (problem children item 1),
  so the web run uses `FLET_FORCE_WEB_SERVER=true FLET_SERVER_PORT=<port> uv run python gui2/main.py`.
  The web server resolves the default `assets` folder next to the script
  (`gui2/assets`), so `gui2/main.py` needs no change. A first try with
  `assets_dir="gui2/assets"` doubled the path (`gui2/gui2/assets`) and was
  reverted. Task 2.2's command is replaced by this form.
- 2026-10-30 web run: preview opens and Save works. Fix: preview body overrides home.css fixed-height flex body (summary box was squeezed when root family opened).
- 2026-10-30 review (Sonnet subagent, CodeRabbit, pi pane): fixed a preview
  failure that blocked saving (now a dialog with the error that still offers
  Save), a double press that could save twice (guard in `preview_and_confirm`
  plus a once-only Save), a duplicate README bullet, and the username in the
  preview file name. Skipped: CodeRabbit's `pop_dialog` (same two steps as the
  current code, and it closes the topmost dialog, not necessarily ours). Added
  flow tests and a Pass1 handler test: with the three guards off, 3 tests fail.
  Not covered by a test: the Pass2Add handler wiring (live run only).
- Final: `tests/` 2664 passed, 12 deselected. `just typecheck` 0 errors.
  2.2 contributor web run: preview opened, Save wrote the contributor JSON and
  not the db. Open: audio button in the preview, see problem children item 10.
