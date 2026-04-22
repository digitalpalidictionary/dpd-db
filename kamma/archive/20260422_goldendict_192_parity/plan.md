# Goldendict #192 Sutta Info Parity Plan

GitHub issue reference: `#192`

## Phase 1: Confirm parity targets and update Goldendict rendering

- [x] Compare the current webapp `#192` sutta-info behavior against the Goldendict headword template
  Files: `exporter/webapp/templates/dpd_headword.html`, `exporter/goldendict/templates/dpd_headword.jinja`, `db/models.py`
  Outcome: a clear list of Goldendict template branches that must match the webapp for `is_vagga`, `is_samyutta`, SC card links, and DV suppression.
  → verify: inspect the template diff and confirm the planned changes are limited to `#192` sutta-info behavior only, with no unrelated exporter churn.

- [x] Update `exporter/goldendict/templates/dpd_headword.jinja` to mirror the current `#192` webapp behavior
  Files: `exporter/goldendict/templates/dpd_headword.jinja`
  Changes applied:
  - Added `{% set is_vagga %}` / `{% set is_samyutta %}` variables at top
  - Button label: `sutta` → `{% if is_samyutta %}saṃyutta{% elif is_vagga %}vagga{% else %}sutta{% endif %}`
  - CST vagga: added `and not is_samyutta`
  - CST sutta: added `and not is_vagga and not is_samyutta`
  - SC heading condition: `{% if d.su.sc_code %}` → `{% if d.su.sc_code or d.su.sc_book or d.su.sc_vagga %}`
  - SC vagga: added `and not is_samyutta`
  - SC sutta: added `and not is_vagga and not is_samyutta`
  - SC eng sutta/title: added `and not is_vagga and not is_samyutta`
  - SC blurb: added `and not is_vagga and not is_samyutta`
  - SC card links: three branches (vagga / saṃyutta / normal) matching webapp exactly
  - BJT heading: expanded condition to match webapp
  - BJT vagga: added `and not is_samyutta`
  - BJT sutta: added `and not is_vagga and not is_samyutta`
  - DV catalogue + parallels: wrapped in `{% if not is_vagga and not is_samyutta %}`
  → verify: render representative aggregate and non-aggregate rows in tests and confirm the HTML contains the expected labels, links, and hidden sections.

- [x] Make any minimal supporting Goldendict data-path change only if the template update alone is insufficient
  Outcome: No Python changes needed — `d.su` already flows through `HeadwordData` with `is_vagga`, `is_samyutta`, `sc_vagga_link` already available on the model.
  → verify: run focused Goldendict tests and confirm no runtime attribute or template-render failures occur.

- [x] Phase 1 verification
  → verify: `uv run pytest tests/exporter/goldendict/ -q` → 20 passed

## Phase 2: Add focused tests for Goldendict `#192` behavior

- [x] Add Goldendict template-render tests for `saṃyutta`, `vagga`, and normal aggregate rows
  Files: `tests/exporter/goldendict/test_dpd_headword.py`
  Outcome: 17 tests across `TestNormalSuttaRow`, `TestVaggaRow`, `TestSamyuttaRow` lock in the current expected Goldendict behavior for `#192` aggregate rows.
  → verify: `uv run pytest tests/exporter/goldendict/test_dpd_headword.py` → 17 passed

- [x] Cover at least one normal non-aggregate row to prevent regressions in standard sutta-info rendering
  Files: `tests/exporter/goldendict/test_dpd_headword.py`
  Outcome: `TestNormalSuttaRow` (4 tests) covers standard single-sutta branch.
  → verify: run above → all 4 pass

- [x] Run lint on the changed Goldendict implementation and tests
  → verify: `uv run ruff check tests/exporter/goldendict/test_dpd_headword.py` → no errors

- [x] Phase 2 verification
  → verify: `uv run pytest tests/exporter/goldendict/ -q` → 20 passed, 0 failed
