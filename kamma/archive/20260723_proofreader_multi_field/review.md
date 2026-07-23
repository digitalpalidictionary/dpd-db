# Review — Proofreader multi-field

## Gates
- ruff check + format: clean (8 touched files)
- pyright: 0 errors (proofreader, paths, gui2, tests)
- pytest tests/tools/: 580 passed (28 proofreader)

## Independent spec audit (fork subagent)
No blocking defects. Verified:
1. `get_db_data` filters correct — meaning_2 excludes populated meaning_1; meaning_lit
   carries meaning_1 context. All three columns are non-nullable `default=""`, so no
   NULL-vs-empty edge.
2. Per-field incremental cache keyed by id, compared to that field's own text, separate
   cache file per field — no cross-field collision.
3. `get_next_correction` preserves reload-under-lock discipline per queue; `next(iter())`
   pops lowest id (id-sorted on save) = original FIFO; `remaining` recomputed after pop.
4. gui2 `_click_pread_button` guards exhausted case and routes `{field}_corrected` into
   the matching `{field}_add`.
5. Explicit row build in `apply_checked_item` averts a latent crash: old `item.copy()`
   would leak the context key into a meaning_lit row and `DictWriter` (extrasaction=raise)
   would throw.
6. meaning_lit prompt emits context + "do not make idiomatic" and the return key matches
   the parsed key.

Outcome: PASS.

## CodeRabbit (uncommitted, --base main)
0 findings across the proofreader files (tools/proofreader.py, tools/paths.py,
gui2/pass2_add_view.py, gui2/toolkit.py, justfile, tests/tools/proofreader/*).
Note: the later `tools/ai_zai_manager.py` error-messaging change was NOT in this
CodeRabbit run (edited after it started) and is being committed in a separate batch.

## Mid-thread additions (user-requested)
- Switched proofreader models: `deepseek-v4-pro` primary, `glm-5.2` backup —
  because the GLM coding-plan endpoint returns 429 code 1305 "service temporarily
  overloaded" (server-side, not quota) during peak, so GLM-primary wasted ~2.3s
  per batch on a doomed probe. Fallback test now asserts the module constants.
- Improved Z.ai error messaging (`_error_detail`) so a 429 surfaces
  `HTTP 429: [1305] ...` instead of the opaque requests string. Separate batch.

## Reflection
Clean generalization of existing single-field machinery. The explicit-row build in
`apply_checked_item` averted a latent DictWriter crash on the meaning_lit path.
No behaviour regressions; both independent reviewers clear.
