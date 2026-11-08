# Review: 20261108_pass1_no_family_compound

**Verdict: PASSED** (2026-11-08)

## Files Changed
- gui2/dpd_fields_lists.py (field removed from PASS1_FIELDS)
- gui2/pass1_auto_controller.py (drops the key from the AI answer before saving)
- gui2/pass1_context.py (field removed from the prompt; old frozen prompt deleted)
- gui2/data/pass1_auto_{ap,bv,cp,pv,vv}.json (key removed, 355 lines deleted)
- gui2/data/pass1_auto_kva.json (untracked, key removed; add by explicit path)
- tests/gui2/test_pass1_auto_controller.py, tests/gui2/test_pass1_context.py
- kamma/threads/20261105_contrib_audio_preview/plan.md (placeholder, owner's choice, clears the spec-gate hook)

## Findings
- CodeRabbit (`--fresh`, run on gui2 and on tests/gui2): 0 findings, not a reused result.
- DeepSeek deepseek-v4-pro, highest reasoning, read-only, code diff only: verdict "no blocking or major issues". Four findings:
  1. Clone skips family_compound while history load keeps it (minor): NOT A DEFECT. A clone is a new entry, and new Pass1 entries should carry no compound family. Re-editing a saved word keeps its own value.
  2. PASS1_FIELDS removal untested (nit): FIXED, `test_pass1_screen_does_not_show_family_compound`.
  3. Data files untested, kva untracked (nit): SKIPPED as a test (one-off cleanup, the controller test guards the source, a live-data test breaks on later local runs). The kva commit note stays in spec.md.
  4. related_entry_dict removal untested (nit): FIXED, `test_related_entries_leave_out_family_compound`.

## Test Evidence
- Controller test failed before the fix (`assert 'family_compound' not in {... 'family_compound': 'loka nāyaka' ...}`), fails with the pop line removed, passes with it.
- Both new tests fail when their change is reverted (2 failed, 9 passed) and pass when restored.
- `uv run pytest tests/gui2/`: 712 passed. ruff check, ruff format, pyright (`--project /dev/null`) clean on all touched Python files. `just typecheck`: 0 errors.
- Data: `rg -c family_compound gui2/data/pass1_auto_*.json` finds nothing.
- Not done: owner's live check (task 3.3) in Pass1 Add.
