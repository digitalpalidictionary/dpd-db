# Review: Add s.4nt.org to sutta links

## Verification (in lieu of a completed CodeRabbit pass)
CodeRabbit review was started via subagent but stopped by the user before
completing. In its place, the design was verified against ground truth:

- Site's actual source repo (github.com/frankksutta/s.4nt, a static GitHub
  Pages export - the committed file tree IS the complete list of valid
  URLs) cloned to `~/MyFiles/2_Resources/Code/s.4nt/`.
- Every one of the 5,114 real `sc_code` rows in `dpd.db` cross-checked
  against that file tree via the actual `s_4nt_link` property - 0
  mismatches.
- 15+ live HTTP spot-checks, all 200 OK.
- CodeRabbit's one earlier valid finding (missing `tha-ap`/`thi-ap` KN book
  codes) was incorporated after being initially wrongly dismissed as a
  hallucination.

## Verification (standard gates)
- ruff check + ruff format + pyright: clean on all touched files.
- `tests/db/test_sutta_info.py` (10 new/updated cases) +
  `tests/exporter/{goldendict,webapp}/test_dpd_headword.py`: 31 passed.

## Outcome: PASS
