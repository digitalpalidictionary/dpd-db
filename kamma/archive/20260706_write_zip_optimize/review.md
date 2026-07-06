## Thread
- **ID:** 20260706_write_zip_optimize
- **Objective:** Measure whether parallelizing the deconstructor's 3 serial GoldenDict/MDict exports is worth it; implement only if the numbers justify it.

## Files Changed
- `exporter/deconstructor/deconstructor_exporter.py` — `prepare_and_export_to_gd_mdict` now dispatches GD-half-1, GD-half-2, and (when `make_mdict`) MDict via `ProcessPoolExecutor`. New `_export_worker` helper isolates each worker's pyglossary cache dir (`tempfile.mkdtemp`, rebinding `glossary_v2.cacheDir`) and captures its console output at the fd level so the parent prints one clean block per export instead of interleaved lines.

## Findings

Independent review (fresh general-purpose subagent, zero prior context) covered the pre-fix implementation: no blocking/major findings. It verified the mutation-hazard neutralization mechanically (traced `ProcessPoolExecutor.submit()` pickling semantics, confirmed each worker gets an independently-unpickled `DictEntry` graph), reproduced all lint/type/test results, and ran its own synthetic n=0/1/2000 sanity script including a forced-exception case to confirm `future.result()` propagates correctly. It missed the pyglossary cache race and under-weighted the console interleaving as "cosmetic" — both surfaced only when the user ran the real exporter manually afterward.

CodeRabbit (`coderabbit review --agent --base main --type uncommitted`): 0 findings.

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major (found post-review, now fixed) | `deconstructor_exporter.py` (pre-fix) | Concurrent GD workers shared pyglossary's global `~/.cache/pyglossary/tmp`; whichever finished first deleted it under the other, logging `no such file or directory` | Latent race: harmless in the observed timing (files already moved before cleanup) but not guaranteed — a slow worker's still-staged CSS/font temp files could be deleted by another's cleanup | Fixed: each worker rebinds `glossary_v2.cacheDir` to its own `tempfile.mkdtemp()` for the export's duration |
| 2 | major (found post-review, now fixed) | `deconstructor_exporter.py` (pre-fix) | `pr.white_tmr()` leaves a line open across workers sharing stdout; concurrent processes interleaved mid-line, producing garbled-looking console output | Reads as a broken build to a human operator, even though output was byte-correct | Fixed: fd-level output capture per worker; parent prints each worker's block whole on completion |
| 3 | minor | `deconstructor_exporter.py` | Partial output on failure: if one export raises, the others still complete and write full files before the exception surfaces | Downstream tooling that infers success from "files exist" rather than exit code could be fooled after a failed run | Accepted, not fixed — edge case, exit code is still correct; noted here for awareness |
| 4 | minor | `tests/exporter/deconstructor/` | No automated test covers `prepare_and_export_to_gd_mdict` itself (existing gap, not introduced by this thread) | All confidence for this function comes from manual/harness runs, not CI | Accepted, not fixed — a full pyglossary round-trip test is heavy for this repo's conventions; out of scope |
| 5 | nit | `deconstructor_exporter.py` | `_export_worker` rebinding a third-party module global (`glossary_v2.cacheDir`) pins to pyglossary 5.4.1 behavior | Silent breakage risk on a pyglossary upgrade if cacheDir usage changes | Documented in the docstring; re-verify on upgrade |

## Fixes Applied
- Findings #1 and #2 (both major) fixed in this session: private per-worker pyglossary cache dir + fd-level output capture. Re-verified: mid-scale byte-parity intact, 2-concurrent-process stress test produced 0 cache-race occurrences (previously reliable), console output confirmed clean/sequential.
- Findings #3, #4, #5 accepted as-is (minor/nit, not blocking).

## Test Evidence
- Independent reviewer (fresh subagent): reproduced `ruff check`/`ruff format --check`/`pyright` clean and `pytest tests/exporter/deconstructor/ tests/exporter/ tests/tools/` → 863 passed, 16 deselected; ran its own synthetic concurrency/exception sanity script.
- CodeRabbit → 0 findings.
- Post-fix: `ruff check` + `ruff format --check` + `pyright` clean; `pytest tests/exporter/deconstructor/ tests/exporter/ tests/tools/` → 863 passed, 16 deselected (unchanged).
- Post-fix parity: mid-scale byte-identical vs pre-change baseline (GD content); full-scale GD content previously verified byte-identical pre-fix and re-spot-checked post-fix at mid scale (full-scale re-run was skipped post-fix per explicit user instruction to stop benchmarking, given the fix's overhead was independently measured at 0.09ms/export — negligible).
- Live user test (`just export-deconstructor`, real DB, real output paths) confirmed complete, correctly-timestamped output in both `exporter/share/` and the configured GoldenDict directory before the fix; this run is what surfaced findings #1/#2.

## Verdict
PASSED
- Review date: 2026-07-06
- Reviewer: independent general-purpose subagent + CodeRabbit + user manual test + Claude (consolidation and post-review fix)
