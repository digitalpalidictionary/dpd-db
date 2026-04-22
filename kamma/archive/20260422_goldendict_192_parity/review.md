## Thread
- **ID:** `20260422_goldendict_192_parity`
- **Objective:** Add Goldendict `#192` sutta-info rendering parity with the webapp for aggregate rows.

## Files Changed
- `exporter/goldendict/templates/dpd_headword.jinja` — ported `#192` aggregate-row sutta-info behavior from the webapp template.
- `tests/exporter/goldendict/test_dpd_headword.py` — added focused Goldendict template-render tests for normal, vagga, saṃyutta, and current saṃyuttapāḷi behavior.
- `kamma/threads/20260422_goldendict_192_parity/spec.md` — thread spec.
- `kamma/threads/20260422_goldendict_192_parity/plan.md` — implementation plan and verification notes.

## Findings
No findings.

## Fixes Applied
- Added one review-time test for the current `saṃyuttapāḷi`-as-`vagga` behavior so the Goldendict parity suite covers that `#192` edge case explicitly.

## Test Evidence
- `.venv/bin/python -m pytest tests/exporter/goldendict/test_dpd_headword.py` → pass (`18 passed`)
- `.venv/bin/ruff check tests/exporter/goldendict/test_dpd_headword.py` → pass
- `.venv/bin/python -m pytest tests/exporter/goldendict/ -q` → pass (`21 passed`)
- `coderabbit review --agent` → started, no findings returned during the review window

## Verdict
PASSED
- Review date: 2026-04-22
- Reviewer: Codex (Kamma review)
