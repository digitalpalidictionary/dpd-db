# Plan — Simplify deconstructor config flags

## Tasks

- [x] 1. `tools/configger.py`: remove `"deconstructor": {"use_premade": ...}` from `DEFAULT_CONFIG` and from `uposatha`, `github_release`, `quick` profiles
      → verify: `rg -n use_premade tools/configger.py` returns nothing
- [x] 2. `tests/tools/test_configger_fixtures.json`: remove the three `["deconstructor","use_premade",...]` entries
      → verify: `uv run pytest tests/tools/test_configger.py`
- [x] 3. `go_modules/deconstructor/main.go`: gate → run iff `generate.deconstructor == yes`
      → verify: `cd go_modules && go build ./...`
- [x] 4. `scripts/build/deconstructor_output_add_to_db.py`: drop the `use_premade` clause from the gate
- [x] 5. `scripts/build/tarball_deconstructor_output.py`: gate → run iff `generate.deconstructor == yes`
- [x] 6. `scripts/build/deconstructor_extract_archive.py`: delete (dead)
- [x] 7. `scripts/bash/generate_components.py`: remove the `extract_archive` + `add_to_db` lines from the local pipeline
- [x] 8. `justfile`: repurpose `decon-on`/`decon-off` to set `generate.deconstructor`
- [x] 9. Lint + test gate: ruff check/format + pyright on every touched `.py`; `uv run pytest tests/tools/ tests/scripts/build/test_deconstructor_output_add_to_db.py`; `go build`

## Notes

- `config.ini` deliberately untouched (global `.ini` rule). User to delete the dead `[deconstructor]` section manually.
