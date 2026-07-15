# Plan: pass2pre "in comps" — surface compound components needing examples

Thread: 20260715_pass2pre_in_comps

## Architecture Decisions

- **Component map lives in `DatabaseManager`** as a lazily built derived
  structure (`compound_components_map: dict[str, list[str]]`, inflection →
  components), gated by `_corpus_gen` like `make_pass2_lists()` — the
  established pattern for corpus-derived sets. Built only when in-comps mode
  is requested (full-corpus pass, tens of MB — don't pay for it when off).
- **The work item is the compound, not the component** (redesigned
  2026-07-15 after three wrong attempts — see spec). `comps_components:
  dict[str, list[str]]` maps each queued compound to its missing-example
  components. `add_comps_entry(word)` runs per book word inside
  `make_all_words_dict()`/`add_sc_words()` so every work item sits at its
  text-order position; the compound's own example/processed status is
  irrelevant — only the component gates. `get_entry_headwords()` extends an
  entry's headwords with the components' headwords and records each one's
  source component in `entry_headword_sources`; the view saves Yes/No via
  `current_source_word()` under the component word. Examples stay
  `\bcompound\b`; display is `[compound] components`.
- No change to the examples data model, file manager, or Yes/No/New/Pass
  flow: a component match is stored keyed by the compound word with the
  component headword's id.
- **No changes to `db/models.py`** — `construction_line1_clean_list` and
  `grammar` already provide everything needed.
- **Deliberately not abstracted**: no recursion, no persistence of the switch,
  no separate file manager — components flow through the existing
  matched/unmatched files.

## Phase 1: Component map in DatabaseManager

- [x] Add `make_compound_components_map()` to `gui2/database_manager.py`:
  iterate `load_corpus()`; for each headword where `re.findall(r"\bcomp\b", i.grammar)`
  and `len(i.construction_line1_clean_list) >= 2`, map every inflection in
  `i.inflections_list_all` → components (`construction_line1_clean_list`
  minus `all_suffixes`, empty strings dropped). Cache with its own
  `_components_gen` generation counter; requires `make_pass2_lists()` first
  (for `all_suffixes`).
  → verify: `uv run pytest tests/gui2/test_database_manager_components.py` —
  new test with a fake corpus: compound headword yields map entries for each
  inflection; non-compound and single-part constructions excluded; suffixes
  stripped; second call with same corpus gen doesn't rebuild (identity check).

## Phase 2: Controller — append components to the queue

- [x] In `gui2/pass2_pre_controller.py` add `in_comps: bool = False` parameter
  to `find_words_with_missing_examples()` and a
  a `self.comps_components: dict[str, list[str]]` attribute. When `in_comps`
  is true, `make_all_words_dict()`/`add_sc_words()` call
  `add_comps_entry(word)` per book word: any compound with ≥1
  `is_missing_example()` component is queued at its text position,
  regardless of the compound's own example/processed status. Yes on a
  component headword is saved under the component word
  (`current_source_word()`); No is saved under the pair key
  `"{compound} + {sub word}"` (`current_unmatched_key()`) and
  `add_comps_entry()` filters missing components by pair, so a No hides
  only that compound+sub word combination. (Redesigned 2026-07-15 twice — work item is
  the compound; then per-component gating + text order + component-keyed
  saves. Temporary `ic()` debug output removed at wrap-up.)
  → verify: unit test `tests/gui2/test_pass2_pre_components.py` with stubbed
  db/file managers: work items in text order, matched compound still queued
  for missing components, decided component not requeued, decisions keyed by
  source word; with `in_comps=False` the queue is unchanged.
- [x] Guard Yes/No clicks against a stale headword index
  (`current_headword()` returns None on double-click race or clicks after
  queue exhaustion; view handlers return early). Fixes IndexError the user
  hit in live use 2026-07-15; also guards the pre-existing unguarded
  indexing in `handle_yes_click`.
  → verify: unit test for `current_headword()` bounds; gui2 tests pass.
- [x] Per-entry headwords and display: `get_entry_headwords(word)` returns
  the compound's own missing-example headwords plus its components'
  headwords (deduplicated by id), used in `load_next_word()`;
  `display_word_in_text()` shows `[compound] components`; example search
  stays `\bword\b` for every entry. (Redesigned 2026-07-15.)
  → verify: unit tests for `get_entry_headwords` (component headwords
  included, deduplication, regular words unchanged), the display format,
  and the unchanged `\bcompound\b` example regex.

## Phase 3: View — the "in comps" switch

- [x] Add `ft.Switch(label="in comps", value=False)` to the top row of
  `gui2/pass2_pre_view.py` (after the "PreProcess Book" button); pass its
  value into `controller.find_words_with_missing_examples(book, paths, in_comps=...)`
  in `handle_book_click`; reset nothing else (session-only state).
  → verify: `uv run ruff check` + `uv run pyright` clean on touched files;
  user manually opens gui2, sees the switch, runs a small book with it off
  (identical behaviour) — full manual run happens in Phase 4.

## Phase 4: Verification & lint gate

- [x] Run the pre-commit trio on every touched file:
  `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright`
  (gui2 is pyright-excluded but not ruff-excluded — fix any pre-existing
  ruff errors in touched files).
  → verify: all three exit clean on `gui2/database_manager.py`,
  `gui2/pass2_pre_controller.py`, `gui2/pass2_pre_view.py`, new test files.
- [x] Run the test suite for affected areas.
  → verify: `uv run pytest tests/gui2/` all pass.
- [x] Manual verification (user): performed live on AN throughout
  2026-07-15 — compound work items surface with `[compound] sub word`
  display, sub word highlighting, pair-keyed Nos, and Yes/No/New/Pass all
  working ("working fine", "working nicely now").
  → verify: user confirmation received.
