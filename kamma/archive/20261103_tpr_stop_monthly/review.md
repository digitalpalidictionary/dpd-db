## Thread
- **ID:** 20261103_tpr_stop_monthly
- **Objective:** Stop every automatic run of the TPR export (CI and local build); keep the code and manual runs until the end of 2026.

## Files Changed
- `.github/workflows/draft_release.yml` — TPR exporter step removed; `tpr_downloads` out of the sync, collect and push loops and the input description.
- `scripts/bash/makedict.py` — TPR exporter removed from `COMMANDS`.
- `tests/tools/test_configger_fixtures.json` — unrelated pre-existing fix: `make_mobile` → `yes` in `uposatha_reset` (matches commit 7a0d638b).
- `docs/integrations/tpr.md` — Extensions and beta instructions replaced by a short "Updates" section.
- `kamma/tech.md` — TPR note replaced with the current state.
- `tools/configger.py` — changed, then reverted in review: no net change.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `tools/configger.py` profiles | Profiles set `make_tpr = no` | The exporter quits unless `make_tpr = yes`, so `just export-tpr` would stop working after a profile reset; the owner chose to keep manual runs | Reverted profiles and fixture to `yes` |
| 2 | minor | `spec.md` item 3 | Said makedict applies `uposatha_reset` on every build | `uposatha_day_reset` returns early on non-uposatha days | Item rewritten (moot after #1) |
| 3 | minor | `db/families/*` | `make_tpr` gates family generation | Only mattered with `make_tpr = no` | Moot after #1 |
| 4 | nit | `docs/integrations/tpr.md` | "Built into" said twice | Repetition | "Updates" section reworded |
| 5 | minor | `spec.md` decisions | Earlier thread said "switch off only after the author's build works" | Contradiction without a record | Decision and PR comment link added |
| — | rejected | `docs/integrations/tpr.md` | "Built into TPR" may be false | The TPR author's PR #279 comment says each TPR database release ships with the latest DPD (release 136 with today's DPD) | No change |

Nits accepted as-is: CI still clones the submodule and `save_i2h_for_tpr` still writes `i2h.tsv` (both on the year-end list); a historical log line in `.claude/commands/pipeline-improvement-queue.md`.

## Fixes Applied
- Findings 1, 2, 4, 5 fixed. `tools/configger.py` is back to its committed content.

## Test Evidence
- `uv run python -c "import yaml; yaml.safe_load(...)"` on `draft_release.yml` (whole file) → pass; `rg -i tpr` on it → only `softprops/action-gh-release`.
- `uv run pytest tests/tools/ tests/exporter/tpr/` (all tools tests + TPR exporter tests) → 828 passed.
- `just typecheck` (whole repo, pyrefly) → 0 errors.
- `ruff check`, `ruff format --check`, `pyright` on `scripts/bash/makedict.py` → clean.
- CodeRabbit `--agent --uncommitted --fresh` (all tracked changes) → 0 findings.
- Independent zero-context reviewer: `rg --hidden` sweep found no other automatic caller; loops' bash and `${!outcome_var}` checked; the three remaining submodule legs byte-identical.

## Not Verified
- The workflow was not run on GitHub; checked by parsing and reading only.
- The owner's local `config.ini` values were not read (not needed now that profiles are unchanged).
- How the TPR app shows DPD to users was taken from the author's PR #279 comment, not tested.

## Verdict
PASSED
- Review date: 2026-11-03
- Reviewer: CodeRabbit + independent Claude subagent; fixes by the implementing session
