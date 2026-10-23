# Plan: preview before save — the webapp view of the unsaved word

**Thread:** 20261023_contrib_3_preview_before_save · **Spec:** `spec.md` (read first)
**GitHub issue:** #215 — commits reference `#215`
**Start only after** `20261023_contrib_2_edits_json` is finished (needs
`gui2/save_router.py::save_headword`; same save handlers).

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

## Phase 1 — Render the preview
- [ ] 1.1 `gui2/preview.py::render_preview(db_session, word) -> str`. Copy the
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
- [ ] 1.2 Write and open: `write_preview(html, username) -> Path` writes
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
- [ ] 1.3 Phase gate: ruff check --fix, ruff format, pyright
      (`--project /dev/null` for gui2/tests files) on touched files + related tests.
      Report only, no commit.
      → verify: all clean. Paste the counts here.

## Phase 2 — Preview dialog in the save flows
- [ ] 2.1 One shared dialog helper (in `gui2/preview.py`) taking an `on_save`
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
- [ ] 2.2 Live local web run as a contributor WITH the user:
      `DPD_GUI2_USERNAME=alice DPD_GUI2_ROLE=contributor-server uv run flet run --web -p 8551 gui2/main.py`
      on a backed-up db. The preview opens in the browser (or via the link) →
      Save writes `additions_alice.json` / `corrections_alice.json` only. Remove
      the test entries after.
      → verify: results logged here, including the popup-block result.
- [ ] 2.3 Phase gate as 1.3 + `uv run pytest tests/`. Report only, no commit.
      → verify: full suite passes. Paste the counts here.

## Phase 3 — Finish
- [ ] 3.1 Update `gui2/README.md` (the preview step before save). Run
      `just typecheck`, full pytest and `graphify update .`.
      → verify: all pass. Paste the counts here.
