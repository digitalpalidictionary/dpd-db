# Plan — stop the monthly TPR export

Spec: `spec.md`. Follows PR #279 (closed).

## Architecture Decisions

- Remove the callers, keep the callee: the exporter and its tests stay until the end of 2026.
- Leave `make_tpr` in the profiles as `"yes"`: the exporter quits unless it is `yes`, and the manual run must keep working. (Review finding; the first version set it to `"no"`.)

## Phase 1 — Stop the automatic runs

- [x] Edit `.github/workflows/draft_release.yml`: input description, sync loop, TPR step, collect env + loop, push loop.
  → verify: `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/draft_release.yml'))"` passes; `rg -n -i 'tpr' .github/workflows/draft_release.yml` returns nothing.
- [x] Remove the exporter from `COMMANDS` in `scripts/bash/makedict.py`.
  → verify: `rg -n tpr scripts/bash/makedict.py` returns nothing; `uv run ruff check` + `ruff format --check` clean.
- [x] ~~Set `make_tpr` to `"no"` in the profiles~~ — reverted in review (breaks `just export-tpr`). `tools/configger.py` is unchanged. Fixture: only the unrelated `make_mobile` fix in `uposatha_reset`.
  → verify: `uv run pytest tests/tools/test_configger.py` passes.

## Phase 2 — Docs

- [x] Rewrite the end of `docs/integrations/tpr.md`: one section saying DPD updates arrive with each new TPR release; remove the Extensions steps and the beta section.
  → verify: read the page; `rg -n -i 'extension|beta' docs/integrations/tpr.md` shows only intended text.
- [x] Replace the TPR note in `kamma/tech.md`.
  → verify: read the line.

## Phase 3 — Check

- [x] Run `just typecheck` and `uv run pytest tests/tools/ tests/exporter/tpr/`.
  → verify: both pass.

## Results (2026-11-03)

- Workflow: YAML parses; the only `tpr` match left is inside `softprops/action-gh-release`. Sync, collect and push loops keep `fdg_dpd`, `bw2`, `sc-data` unchanged.
- `makedict.py`, `configger.py`: ruff, ruff format, pyright clean.
- `just typecheck`: 0 errors.
- `uv run pytest tests/tools/ tests/exporter/tpr/`: first run 827 passed, 1 failed (`test_profile_matches_original_script_writes[uposatha_reset]` on `make_mobile`, pre-existing since commit 7a0d638b). After the fixture fix and the review's profile revert: 828 passed.
- Docs: `docs/integrations/tpr.md` now ends with an "Updates" section; five screenshots there are unused and added to the year-end list in spec.md.
