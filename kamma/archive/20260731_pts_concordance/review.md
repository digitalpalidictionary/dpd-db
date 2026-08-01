# Review: PTS references from the PTS↔CST concordance into sutta_info

Reviewed 2026-07-31 by an independent subagent (fresh context, read-only) after the
user confirmed acceptance testing. CodeRabbit was deliberately not run (user's call).

## Verification re-run by the reviewer
- `uv run pytest tests/db/suttas tests/exporter/webapp/test_dpd_headword.py
  tests/exporter/goldendict/test_dpd_headword.py` → 49 passed (53 after the fixes).
- ruff check + ruff format --check + pyright clean on every touched file;
  `just typecheck` 0 errors.
- Coverage independently reproduced on a read-only copy of `dpd.db`.

## Findings and disposition

### 1. BLOCKER — skip guard made the feature a no-op on incremental runs. FIXED.
`table_rebuilt` is False whenever the Google Sheet is unchanged and `sutta_info` is
already populated, i.e. the normal incremental run. The guard would therefore have
left `dv_pts` holding its 1,706 old DV-format values indefinitely; the concordance
would only land on a full rebuild. The spec's rationale ("the existing values still
stand") is true only *after* the concordance has been applied once — precisely wrong
for the transition this thread creates.

Fix: the guard and the `table_rebuilt` parameter are gone; the step runs
unconditionally (local, deterministic, idempotent, ~0.3 s). `suttas_update.main()`
now calls `update_pts_concordance_in_db(pth)`. The skip test was replaced with
`test_stale_dv_reference_is_overwritten_on_an_incremental_run`, which asserts a row
still holding `D i 47` becomes `D i 47,3`. spec.md and plan.md updated.

### 2. Blanket `except Exception` around the commit. ACCEPTED AS IS.
A locked db would print red and let the build continue with exit code 0. Real, but
it is verbatim the existing `update_dv_fields_in_db` pattern, and changing failure
semantics for one enrichment step while its sibling keeps the old behaviour is worse
than the inconsistency. Logged as a candidate for a sweep across all enrichment
steps, not fixed here. The reviewer's point that the blast radius is now larger
(this is the sole PTS source) is fair and is why it is written down rather than
dropped.

### 3. Range `cst_paranum` never joined — undocumented fourth miss category. FIXED.
121 rows store `cst_paranum` as a range (`651-662`); the TSV keys on a bare start
paragraph, so those rows always missed. The step now retries on the start of the
range, recovering 92 rows — 3 template-visible (`AN5.257` → `A iii 272,11`,
`AN5.294` → `A iii 276,29`, `AN10.156` → `A v 248`), the rest vagga/saṃyutta rows
that do not display PTS. Coverage 4,384 → **4,476 rows**. New test:
`test_range_paranum_falls_back_to_its_start_paragraph`. spec.md and plan.md updated.

### 4. Vagga/saṃyutta suppression was untested. FIXED.
Both docs promise the gate is preserved, but nothing asserted it — a later edit
hoisting the PTS block above the gate would have passed every test. Added
`test_dpd_headword_vagga_row_hides_pts_and_its_heading` (webapp, real `SuttaInfo`),
`TestVaggaRow::test_pts_hidden` and `TestSamyuttaRow::test_pts_hidden` (goldendict).

### 5. Goldendict PTS test is weak w.r.t. the `dv_exists` change. ACCEPTED AS IS.
`_minimal_su` passes `dv_exists` in as a literal, so that file's
`assert "Dhamma Vinaya Tools" not in html` only proves the stub default is falsy.
The webapp counterpart uses a real `SuttaInfo`, where `dv_exists` is the actual
`cached_property`, so the model change *is* genuinely covered — by that test, not
this one. Rewriting the goldendict harness to use real ORM objects is out of scope.

### 6. `cell()` blanks only `float` NaN, not `pd.NA`/`pd.NaT`. ACCEPTED AS IS.
Unreachable with the current sheet (object columns come back as float NaN) and the
blank-cell test passes. A `pd.isna()` call is what pyright rejects here, which is
how the narrow check arose. Latent only.

### 7. plan.md claimed a `--path` flag. FIXED (wording).
`main()` takes a bare positional path, not `--path`. plan.md corrected.

## Categories the reviewer cleared
- Duplicate-key tie-break behaves exactly as documented; the artefact has 4,467
  rows, zero duplicate keys, correct sort order, no blank `pts_ref`, uniform 7
  columns, and no tab/newline/quote injection is possible.
- No template branch can produce a dangling PTS row or an empty PTS heading.
- No stray ORM mutation: only `dv_pts`, only on rows deliberately updated.
- No dead code or unused imports.

## Post-fix state
`uv run pytest tests/` → 1,768 passed, 12 deselected. `just typecheck` → 0 errors.
ruff + pyright clean on all touched files. Smoke on `/tmp/dpd_pts_test.db`: 4,476
rows populated (from 1,706), `AN3.48`/`AN3.63` the only rows to lose a previous ref,
live `dpd.db` md5 unchanged.
