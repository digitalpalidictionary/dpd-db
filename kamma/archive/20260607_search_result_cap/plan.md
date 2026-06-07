# Plan

## Architecture Decisions
- Cap applied at the GUI layer (rendering) + an OPTIONAL `limit` on the commentary
  DB query. The shared search functions keep their default (unlimited) behavior so
  webapp/analysis callers are untouched.
- Detect "there are more" by fetching `CAP + 1` rows (commentary) or checking
  `len(full_list) > CAP` (sutta) — no extra COUNT query.
- Module-level constant `MAX_SEARCH_RESULTS = 50` in each gui2 field file.

## Phase 1: Bound the commentary DB query
- [x] In `tools/bold_definitions_search.py`, add `limit: int | None = None` to
      `search()`. Build one query object, apply filters per option, apply
      `.limit(limit)` only when `limit is not None`, then `.all()`. Behaviour for
      existing callers (limit omitted) unchanged.
  → verify: `uv run pyright tools/bold_definitions_search.py`; webapp call
    `search(q1, q2, option)` still returns all results.

## Phase 2: Commentary GUI cap + notice
- [x] In `gui2/dpd_fields_commentary.py`: add `MAX_SEARCH_RESULTS = 50`. In
      `click_commentary_search`, call `search(..., limit=MAX_SEARCH_RESULTS + 1)`.
      Compute `truncated = len(self.commentary_list) > MAX_SEARCH_RESULTS`, then
      trim `self.commentary_list` to `MAX_SEARCH_RESULTS`.
- [x] In `choose_commentary`, when `truncated`, prepend a notice Text row.
  → verify: search "sam" → dialog opens instantly with 50 entries + notice; index
    alignment in `click_choose_example_ok` still correct.

## Phase 3: Sutta example notice
- [x] In `gui2/dpd_fields_examples.py`: add `MAX_SEARCH_RESULTS = 50`, replace the
      `[:50]` literal with the constant, and when
      `len(self.cst_examples) > MAX_SEARCH_RESULTS` prepend the same refine-search
      notice to the dialog.
  → verify: search a common term → 50 radios + notice; `example_index` selection
    still resolves via `self.cst_examples[int(...)]`.

## Phase 4: Gate
- [x] `uv run ruff check --fix` + `ruff format` + `pyright` on all 3 files.
- [x] `uv run pytest` for any related tests.
  → verify: all green.
