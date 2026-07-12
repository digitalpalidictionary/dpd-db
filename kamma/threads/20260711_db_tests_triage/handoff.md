# Handoff: db_tests triage & refresh

**Written:** 2026-07-12 evening, mid-Phase 4.

## Current state

Phase 4 row 1 done and user-confirmed: `db_tests/db_tests_relationships.py`
— verdict **keep + improve**, fully implemented (streaming results,
`load_only` on 24 columns, dead `dpd_roots`/`compound_families` queries
dropped, gui2 db tab regex added underneath the db browser regex, 3
redundant FIXME blocks deleted, double `root_sign_x_base_mismatch` call
deduped via new module-level `TESTS` registry, modern typing, header
tidy). Behavior verified: per-test counts identical 31/31 on a bench db
copy; user ran `just db-test` and confirmed. ~2s to first prompt, was
~6.6s. Details in `plan.md`.

**Uncommitted** — user commits everything themselves. Changed by this
session: `db_tests/db_tests_relationships.py`, `plan.md`, this file.
(`db_tests/db_tests_columns.tsv` was already modified before the session
— live gui2 data, not this thread's work, leave alone.)

## Next task

Next unticked row in `plan.md` Phase 4 (final file row of the thread):

```
- [ ] `db_tests/db_tests_manager.py` — `DbTestManager`: loads/checks/runs/saves the column-rule TSV
  - shared library · writes the TSV (not the DB) · refs: gui2 ×4 + `tests/db_tests/test_db_tests_manager.py` (158 lines) · last run: 2026-06-16 (live via gui2) · git: 2026-06-15 · flags: mixes bare rich `print("[red]...")` with `pr.red(...)`; `main()` is a hardcoded id=112 smoke demo
  - verdict: ____ (constraint: gui2-facing API must not break)
```

Standard triage flow: user runs/reports (it's a library — exercised live
via gui2's Tests tab; also has real pytest coverage in
`tests/db_tests/test_db_tests_manager.py`), verdict recorded, then
implement + freshen. HARD CONSTRAINT: gui2-facing API must not break
(imported by gui2/toolkit.py, test_manager.py, tests_tab_controller.py,
tests_tab_view.py).

Then: **Phase 4 wrap** (`uv run ruff check db_tests/` + `uv run pyright
db_tests/` + `uv run pytest tests/`), then Phase 5 (pycache cleanup,
READMEs, final sweep).

## Loose ends / notes for next session

- Phase 1 has one still-unverdicted row parked earlier by the user:
  `db_tests/single/test_gram_in_last_position.py` (verdict blank).
  Surface it before closing the thread.
- Phase 3's `db_tests/gui/add_antonyms.py` row is `[~]`: implementation
  done, waiting on the user to launch `db_tests/gui/main.py` and confirm
  the "Add antonyms" flow incl. Exception button end-to-end.
- `sandhi_contraction_errors` in db_tests_relationships.py stays parked
  (commented entry in `TESTS` with reason) — user never chose
  re-enable/delete; ask again at Phase 4 wrap if it matters.
- `pos_idiom_no_space_is_sandhi` solution text flipped to "change pos to
  idiom" (was self-contradictory) — user hasn't explicitly confirmed the
  intent reading; it printed fine in their `just db-test` run.
- Benchmark artifacts live in the session scratchpad (bench_current.py,
  bench_loadonly.py, verify_rewrite.py, dpd_bench.db 2.26 GB copy) —
  scratchpad is session-specific, nothing to clean in the repo.
- Smoke suite note: `uv run pytest tests/` had 3 pre-existing failures
  unrelated to this thread (DB-content drift golden-master tests, see
  Phase 2 `add_synonym_variant_del.py` row) — don't re-investigate
  unless they get worse.
- Model: Phase 4's remaining row is API-preserving library work — keep a
  strong model (this session ran Fable 5).

Resume with `/kamma:2-do db_tests` (or the thread id).
