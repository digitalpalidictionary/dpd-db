# Plan: gui2 "sp" spelling find/replace tab

Spec: `./spec.md`

## Architecture Decisions
- **Pattern to follow:** `gui2/sandhi_find_replace_view.py` (`SandhiFindReplaceView`)
  is the direct template — the new view is a trimmed variant of it. New file:
  `gui2/spelling_find_replace_view.py`, class `SpellingFindReplaceView`, with an
  inner `Data` class mirroring the sibling's DB-walk state.
- **Raw regex, not escaped:** unlike the `'` tab, the Find term is passed to the DB
  `regexp_match` and to Python `re` verbatim (no `re.escape`), enabling `\b`, classes
  and backreferences. Compile the pattern once on Find; on `re.error` show a message.
- **Per-field replace-all:** Commit applies `re.sub(pattern, replace, field_text)` to
  the whole field at once. No per-occurrence cursor engine, no editable Replaced field.
- **No Phase 2:** the bold/tag search and the editable-field machinery from the
  sibling are dropped entirely.
- **Highlighting via `re.finditer`, not `re.split`:** `re.split` on a pattern with
  capturing groups corrupts spans; a single `finditer` pass builds both the Found
  (`match.group(0)`) and Replaced (`match.expand(replace)`) highlight spans, and the
  Replaced preview equals the `re.sub` that Commit applies.
- **Place tab after `'`:** insert "sp" at index 9 in `main.py`'s `tab_labels` and
  `_view_builders`, renumbering Sandhi…CT (down by one) and `_warmup_tab_order` to
  match. (User chose visual adjacency over the no-renumber append.)
- **Fields:** `meaning_1`, `meaning_2`, `meaning_lit`, `notes` (English prose only).

## Phase 1 — The view

- [x] Create `gui2/spelling_find_replace_view.py` with `SpellingFindReplaceView`
  (subclass `ft.Column`) and an inner `Data` class, adapted from
  `SandhiFindReplaceView` / its `Data`:
  - `Data.columns = ["meaning_1", "meaning_2", "meaning_lit", "notes"]`.
  - `Data.search_db(pattern)` filters `DpdHeadword` with `or_(...regexp_match(pattern))`
    over the four columns using the **raw** pattern (no `re.escape`).
  - Keep `refresh_db_session`, `commit`, `index`/`column_index` walk, `this_headword`,
    `this_field_name`, `this_field_text` as in the sibling.
  - UI: Find field, Replace field, strip switch (default on), Find + Clear buttons,
    message line, Found (Text w/ spans) and Replaced (Text w/ spans), Commit + Ignore
    buttons. Drop the editable `replaced_field_input` and the mode-switch logic.
  - `find_clicked`: strip if switch on; require Find non-empty (Replace may be empty);
    `try: re.compile(pattern)` and on `re.error` set message and return; then search.
  - `_load_next_result`: skip fields where `re.search(pattern, text)` is None; on a
    match, render Found/Replaced spans and the counter line
    (`{index+1}/{len} {lemma_1} ({id}) {field}`); at end, reset + message.
  - `commit_clicked`: `new = re.sub(pattern, replace, this_field_text)`;
    `setattr(this_headword, this_field_name, new)`; `data.commit()`;
    `toolkit.db_manager.mark_corpus_stale()`; advance.
  - `ignore_clicked`: advance only.
  - `_highlight_found` / `_highlight_replaced`: build spans from one
    `re.finditer(pattern, text)` pass (see Architecture Decisions).
  → verify: `uv run ruff check gui2/spelling_find_replace_view.py` and
    `uv run pyright gui2/spelling_find_replace_view.py` are clean.

- [x] Wire the tab into `gui2/main.py`:
  - Import `SpellingFindReplaceView`.
  - Insert `"Sp"` into `tab_labels` immediately after `"'"` (index 9).
  - Add `9: lambda: SpellingFindReplaceView(self.page, self.toolkit)` to
    `_view_builders` and renumber Sandhi…CT down by one (→ 10…15).
  - Renumber `_warmup_tab_order` to the shifted indices and include 9 (after 8).
  → verify: `uv run ruff check gui2/main.py` clean (gui2 is pyright-excluded);
    labels ↔ builders aligned (sp=9, `'`=8), warmup covers 1–15 exactly once.

## Phase 2 — Regression tests (logic only)

- [x] Add `tests/gui2/test_spelling_find_replace_view.py` and
  `tests/gui2/test_sandhi_find_replace_view.py`. Logic only — no live db, no Flet
  page runtime: monkeypatch each module's `get_db_session` so `Data()` constructs
  without connecting, and stub the view instance's `update()` so highlight methods
  can run unmounted.
  - `Data`: assert `columns` (the searched field list) and the `increment()`
    field→row walk, including the end-of-walk sentinel (`index == len(db_results)`),
    plus `this_field_name` / `this_field_text` against fake `DpdHeadword` objects.
  - Spelling view transforms: `_highlight_replaced` / `_highlight_found` with
    `find_me=r"\bcognise\b"` on `"recognise ... cognise"` change only the whole word
    (proves raw regex), and a backreference case (`(\w+?)ise\b` → `\1ize`) proves
    `match.expand`. Reconstruct the full replaced string from the spans and assert it
    equals the `re.sub` result.
  - Sandhi view: a literal-term highlight to guard span structure (not its regex
    quirks) + the `Data` walk.
  → verify: `uv run ruff check tests/gui2/test_*find_replace_view.py` clean;
    `uv run pytest tests/gui2/test_spelling_find_replace_view.py
    tests/gui2/test_sandhi_find_replace_view.py -q` all pass.

- [ ] Phase-end verification.
  → verify: user launches gui2, opens the **sp** tab, runs Find `\bcognise\b` /
    Replace `cognize`: affected fields preview with the whole word highlighted;
    **Commit** rewrites the field (re-Find shows it gone), **Ignore** skips it, and no
    "recognise" is altered. An invalid regex (e.g. `[`) shows an error, no crash.
    Confirm the `'` and Sandhi tabs still work. (App launch is the user's to run.)
