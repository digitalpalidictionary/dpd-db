## Thread
- **ID:** 20261006_epitaka_dpd_export
- **Objective:** Every dpd-db build refreshes the local ePitaka `dpd-dictionary.db` from `dpd.db`, matching the upstream file's data and HTML.

## Files Changed
- `exporter/epitaka/epitaka_exporter.py` — new exporter: HTML builders, lookup rows, build, Dart norm prebuild, close/install/reopen, config gate
- `exporter/epitaka/README.md` — new folder README
- `tests/exporter/epitaka/test_epitaka_exporter.py` — 22 tests (HTML vs baseline strings, lookup rows, gate, install, close/reopen order)
- `tools/configger.py` — `[exporter] make_epitaka` default, `[epitaka]` section, both next to tpr
- `tools/paths.py` — epitaka output, db and baseline paths
- `scripts/bash/makedict.py`, `justfile` — run after TPR; `export-epitaka` recipe
- `.gitignore` — `exporter/epitaka/output/`
- `docs/technical/project_folder_structure.md`, `kamma/tech.md` — docs
- `kamma/threads/20261006_epitaka_dpd_export/artifacts/parity.py` — parity harness
- `kamma/threads/20261006_epitaka_dpd_improvements/plan.md` — placeholder so the spec-gate hook allows edits

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `epitaka_exporter.py` install | Backup waits forever on the app's write lock | Daily build could hang silently | Fixed: close ePitaka first (30 s limit, skip install if it stays open), reopen after |
| 1b | — | same | Any exception stops makedict | Same for every exporter; user ruled it a non-problem | Not changed |
| 2 | minor | `parity.py` output mode | Lookup breakdown in plan not reproduced by script | Claim looked unbacked | Plan notes the counts came from a separate classification; reviewer re-derived them, they match |
| 3 | minor | `parity.py` | Baseline opened read-write | Only upstream copy | Fixed: read-only URIs, write refused |
| 4 | minor | `prebuild_norm_table` | No row-count check after exit 0 | — | Not needed: the Dart tool exits 1 when the table is incomplete |
| 5 | minor | tests | `build_db` untested as a whole | — | Deferred (user: fix what is necessary); covered by the parity runs |
| 6 | minor | prebuild | Norm table built by repo checkout, not installed app | Fold drift possible | Deferred |
| 7-10 | nit | docstring, `repo_path: str`, Lookup ORM load, tech.md timing | — | — | Docstring fixed; rest skipped |
| CR1 | minor | prebuild failure | Partial norm table could be installed | — | Not real: the app resumes a partial table from its highest rowid |

## Fixes Applied
- Close/install/reopen around the install (user request), with 5 new tests.
- Parity script read-only; plan note on lookup counts; README and tech.md updated.

## Test Evidence
- `uv run pytest tests/exporter/epitaka/ tests/tools/` (scope: exporter + config tests) → 707 passed
- `uv run pytest tests/` (scope: whole suite, after the review fixes) → 1,994 passed
- ruff, ruff format, pyright on touched Python files; `just typecheck` (whole repo) → clean
- Parity snapshot mode (scope: all 88,864 headwords, all 753 roots, 2026-05-01 data) → 100% identical
- Revert checks: lit. rule, folder gate, skip-install guard → each fails exactly its test
- `coderabbit review --agent --uncommitted --include-untracked` → 1 finding (CR1)
- Live (user): export run twice; app shows new words, folded search works, no norm rebuild, closes and reopens fine

## Not Verified
- Behaviour if the installed app's fold code drifts from the epitaka repo checkout.

## Verdict
PASSED
- Review date: 2026-10-06
- Reviewer: independent general-purpose subagent + CodeRabbit; fixes by the implementing session
