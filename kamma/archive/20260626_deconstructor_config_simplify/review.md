# Review — Simplify deconstructor config flags

**Verdict: PASS**

## Scope reviewed
Full diff across `tools/configger.py`, `tests/tools/test_configger_fixtures.json`, `go_modules/deconstructor/main.go`, the three `scripts/build/` deconstructor scripts (one deleted), `scripts/bash/generate_components.py`, `justfile`.

## Correctness
- **go gate**: `doNotRun = !IniTest("generate","deconstructor","yes")` → Go runs locally iff `generate=yes`; CI never invokes Go. Correct.
- **tarball gate**: `if not config_test("generate","deconstructor","yes")` → runs iff `generate=yes`. Polarity flip from the old `use_premade==yes → skip` is correct (tarball belongs to the regenerate path).
- **add_to_db gate**: `use_premade` clause dropped; `generate==no → skip`. CI still loads premade because CI `generate` defaults to `yes`. Unused `config_test` import removed.
- **profiles/defaults**: `use_premade` removed from `DEFAULT_CONFIG` and `uposatha`/`github_release`/`quick`; fixtures JSON updated to match. `test_profile_options_have_defaults` still holds (no profile references a missing default).
- **extract_archive.py**: deleted — only the local pipeline referenced it; CI extracts inline with `tar`. No remaining references.

## CI safety
`config.ini` is gitignored and regenerated from `DEFAULT_CONFIG` (`generate.deconstructor` default `yes`); `github_release` profile does not touch `[generate]`. CI's `deconstructor_output_add_to_db.py` step keeps loading premade. No regression.

## Gate results
- ruff check + format: clean
- pyright: 0 errors on all touched `.py`
- `go build` / `go vet`: clean
- pytest: 17 passed (`test_configger.py`, `test_deconstructor_output_add_to_db.py`)
- `rg use_premade` over source: no hits

## Notes / follow-ups
- `config.ini` left untouched (global `.ini` rule); dead `[deconstructor]` section to be removed manually by the user — harmless.
- `generate_components.py` working tree also contains unrelated user comment-outs (local run-subset state), independent of this thread.
- Suggested commit: `#157 deconstructor: simplify config to two flags, drop use_premade`
