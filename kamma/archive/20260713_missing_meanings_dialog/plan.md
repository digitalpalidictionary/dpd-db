# Plan: missing words dialog + "eg" queue in gui2

**Thread:** 20260713_missing_meanings_dialog
**Spec:** `spec.md` in this folder

## Architecture Decisions
- **Separate eg queue, not the "New" queue** — keeps eg-mined words out of the organic new-word
  flow; new `gui2/pass2_eg_manager.py` follows the `Pass2NewWordManager` pattern (JSON dict,
  atomic save, pop-first) rather than subclassing it, since the entry shape differs (arbitrary
  prefill dict + origin comment).
- **Per-field scanning** (3 calls to `find_missing_meanings`, one per source field) instead of
  one combined-text call, so each missing word carries the correct sentence context.
- **Two-mode "Eg" load** — existing headword → edit mode (X-button pattern); unknown word →
  new-word mode (New-button pattern). Prevents accidental duplicate headwords.
- **No ignore list** (reversed 2026-07-14 after testing) — skipping is a per-sentence decision,
  not a property of the word; unticked words simply aren't added and will reappear if found in
  another sentence. A manual ignore list is deferred until noise proves real.
- `find_missing_meanings` imported as-is from `scripts.find.missing_meanings` — not copied, not
  modified.

## Open questions (defaults taken while user was AFK — confirm at Task 1)
1. Criteria level 3 (missing meaning_1 OR example_1)? — default **yes**
2. Fire on both add and update branches? — default **yes**
3. Persistent ignore file? — implemented, then **removed** after user testing (see above)
4. Two-mode eg loading? — default **yes**

## Phase 1 — eg queue storage

- [x] Confirm the four defaults above with the user.
  - → verify: user confirmed all four defaults ("lets try it", 2026-07-14).

- [x] Add `pass2_eg_words_path` to `gui2/paths.py` (`gui2/data/pass2_eg_words.json`).
  (`pass2_eg_ignore_path` was also added, then removed with the ignore feature.)
  - → verify: `uv run ruff check gui2/paths.py` clean. ✓

- [x] Create `gui2/pass2_eg_manager.py`  <!-- constructed directly in Pass2AddView (not ToolKit) to keep touched files minimal --> with `Pass2EgManager`: `add_word(word, prefill: dict,
  comment)`, `get_next() -> tuple[str | None, dict | None]` (pop-first, like
  `Pass2NewWordManager.get_next_new_word`), `is_queued(word) -> bool`, atomic JSON save.
  Model on `gui2/pass2_pre_new_word_manager.py`. (Ignore methods removed with the feature.)
  - → verify: quick REPL/pytest smoke — add, get_next pops and persists across reload;
    `uv run ruff check` + `ruff format` clean. ✓ (scratchpad smoke "smoke OK", lint clean)

## Phase 2 — scan + dialog on save

- [x] In `gui2/pass2_add_view.py::_click_add_to_db`, inside `if committed:` (after
  `request_dpd_server`), scan `word_to_save.example_1`, `.example_2`, `.commentary` each with
  `find_missing_meanings(db_session, text, level=3)`; build `{word: prefill_dict}` per spec
  mapping (ex1→`_1` fields, ex2→`_2` fields as source_1/sutta_1/example_1, commentary→
  `{commentary: text}`); dedup across fields; drop words where `is_known()` or word == saved
  lemma. Skip entirely on empty result.
  - → verify: manual smoke — save a word with known-missing words in its example text; a
    populated dict is produced; save of a fully-covered word produces nothing.

- [x] Build the missing-words `ft.AlertDialog` (follow `delete_alert` pattern ~line 881): per
  row a pre-checked `ft.Checkbox` + word as clickable text button calling
  `request_dpd_server(word)`. Actions: "Add ✓ / Ignore ✗" (ticked → `add_word`, unticked →
  nothing for unticked) and "Close" (no side effects). Refined after testing: checkboxes
  unticked by default, words grouped under their source sentence (shown, selectable) in
  appearance order, plain selectable text instead of buttons, bold tags stripped from prefills,
  action renamed "Add ticked".
  - → verify: dialog lists correct words; clicking a word opens it in the webapp; Close leaves
    both JSON files untouched.

- [x] Wire "Add ✓ / Ignore ✗" and confirm persistence + re-suppression.
  (code complete; in-app confirmation folded into Phase 4 manual golden path)
  - → verify: ticked words appear in `pass2_eg_words.json` with comment `eg: found in <lemma>`;
    unticked words untouched; already-queued words don't reappear in the dialog.

## Phase 3 — "Eg" button

- [x] Add `self._eg_button = ft.ElevatedButton("Eg", ...)` after `self._x_button` (construction
  ~line 118, row placement ~line 205), with count tooltip via `_update_count_tooltip` like
  siblings.
  - → verify: button renders next to X in the running app.

- [x] Implement `_click_eg_button`: pop `get_next()`; resolve word against db via exact
  `get_headword_by_lemma` match (sufficient — `find_missing_meanings` returns `lemma_1` values
  for existing headwords, so no `lookup` fallback needed) → edit mode per `_click_x_button`;
  no match → new-word mode per `_click_load_new_word` (clear + `update_add_fields(prefill)`,
  word into `lemma_1`). Shows remaining count; "No more eg words" when empty.
  - → verify: manual — queue one existing-but-meaningless word and one unknown word; Eg loads
    the first in edit mode with db fields populated, the second as a prefilled new word.

## Phase 4 — lint + end-to-end verification

- [x] Lint gate on all touched files — ruff check/format clean, pyright 0 errors on all three
  files; full pytest run: 1719 passed, 3 pre-existing failures unrelated to gui2 (stale golden
  data in tests/db/families/test_family_root.py + tests/exporter/txt/test_export_txt.py vs
  current dpd.db).: `uv run ruff check --fix`, `uv run ruff format`, and run
  `uv run pyright` noting pre-existing errors (gui2 pyright-excluded — note, don't skip) for
  `gui2/pass2_add_view.py`, `gui2/pass2_eg_manager.py`, `gui2/paths.py`.
  - → verify: ruff clean on all three; pyright output noted.

- [x] **Manual golden path (required — Flet UI):** exercised by the user across several live
  iterations on 2026-07-14 (dialog appearance, word selection, ticking, Eg loading in both
  modes), driving the refinements recorded above. User verdict: "ok i'm happy".
  - → verify: user confirmation received 2026-07-14.

## Review (2026-07-14)
- Sonnet subagent review stalled repeatedly on infrastructure (no findings delivered);
  replaced by an inline adversarial audit in the main session: no blocking defects.
  Minor accepted observations: (a) a just-saved new word's own inflected forms can appear as
  "missing" until the lookup table is rebuilt; (b) words <4 chars sort to the end of their
  section in appearance ordering; (c) one small query per unique word at save time (fine for
  SQLite). CodeRabbit run skipped per user instruction.
- Thread finalized and archived 2026-07-14 (verdict: PASSED — see review.md).

---

## Notes
- `scripts/find/missing_meanings.py` verdict in `20260713_scripts_triage`: **keep as library,
  integration tracked here** — do not archive it there.
- `find_missing_meanings` prints its result to console (rich) — acceptable noise; do not modify
  the script in this thread.
