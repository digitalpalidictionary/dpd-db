# Review: 20261011_pass1_add_suggestions

**Verdict: PASSED** (2026-10-11, after the review fixes below were applied and live-checked by the user)

## How the review ran
Two parallel Sonnet subagents, read-only:
1. A from-scratch spec/code audit against `spec.md`.
2. CodeRabbit CLI: `coderabbit review --agent --uncommitted --include-untracked`, once with `--dir gui2` and once with `--dir tests/gui2`.

## Files Changed
- `gui2/dpd_fields.py`: one comment reworded, no code change.
- `gui2/pass1_add_controller.py`: `SOURCE_TEXT_FIELDS`; `load_into_gui` splits AI keys → `update_add_fields`; `process_book` clears the form first; post-save message uses `word_in_text`.
  (This file also holds another thread's uncommitted hunk in `__init__`: the `VariantReadingFileManager` / `SpellingMistakesFileManager` path arguments. That hunk is not part of this thread.)
- `gui2/pass1_add_view.py`: `include_add_fields=True`; History load clears `_add` without resetting flags; button label "Add to Spelling".
- `tests/gui2/test_pass1_add_controller.py` (new)
- `tests/gui2/test_pass1_add_view.py` (new)

## Findings
1. CodeRabbit, major: History load used `clear_fields(target="add")`. Its `flags.reset()` let the blur helpers overwrite the saved stem/pattern/lemma_2. A regression from task 2.3. **Real.**
2. Sonnet audit, should-fix: Process Book loaded without clearing, so stale `_add` values could stay beside the new word. **Real.**
3. Sonnet audit, nit: the spec's "rebuild" claim omitted Process Book. **Real (wording).**
4. Sonnet audit, nit: the test fakes `DpdFields`, so it proves the split, not button state. **Accepted.**

## Fixes Applied
1. History clears with `update_add_fields({config.name: "" ...})`. New test `test_pass1_add_view.py`.
2. `process_book` calls `self.ui.clear_all_fields()` first.
3. The spec is updated.

## Test Evidence
- `uv run pytest tests/gui2/`: 368 passed (baseline before the thread: 364).
- Revert checks: load split reverted → 1 of 2 failed (`assert 'narena' is None`). History fix reverted → 1 of 2 failed (`stem_pattern_done` False).
- ruff check, ruff format, and pyright are clean on all touched files. `just typecheck`: 0 errors.
- Live (user): first run "all good"; saved `sumanadevīvatthu` id 90246 holds the user's edited values, not the raw AI suggestions. Re-check after the fixes: "all checks out".
