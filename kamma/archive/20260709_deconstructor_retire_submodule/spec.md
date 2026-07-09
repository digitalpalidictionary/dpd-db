# Spec: Retire the `resources/deconstructor_output` submodule system

## Context

The deconstructor streaming refactor (thread `20260708_deconstructor_ci_memory`,
merged to main) wired CI and local builds to generate `deconstructor_output.json`
live via `go run go_modules/deconstructor/main.go` →
`scripts/build/deconstructor_output_add_to_db.py`. The old premade-artifact
path — a maintainer locally regenerating the JSON, tarballing it, committing to
the `resources/deconstructor_output` git submodule, and CI unzipping that
tarball — is now superseded. The submodule, the tarball script, and all their
references are dead surface area that must be removed.

## Complete carrier list (verified by exhaustive `rg --hidden` sweep)

Every file that references the premade submodule path and must be modified or
deleted:

| File | Lines | What to do |
|------|-------|------------|
| `.gitmodules` | 13-15 | Remove `[submodule "resources/deconstructor_output"]` block |
| `.git/config` | 26-27 | Removed automatically by `git submodule deinit` |
| `tools/paths.py` | 306, 320-325 | Remove 3 attrs: `deconstructor_output_dir`, `deconstructor_output_json`, `deconstructor_output_tar_path` + the `# resources/deconstructor_output` comment block |
| `tools/tarballer.py` | 109-112 | Remove the dead `create_tarball` call site for the deconstructor tarball. **Keep `create_tarball` function** — `audio/db_create.py:21,180` calls it for a different tarball |
| `scripts/build/tarball_deconstructor_output.py` | entire file (51 lines) | Delete — dead script, no live caller |
| `scripts/onboarding/contributor_setup.py` | 31 | Remove `"resources/deconstructor_output"` from `REQUIRED_SUBMODULES` |
| `scripts/project_management/project_health_check.py` | 23 | Remove `"deconstructor_output"` from `ACTIVE_REPOS` |
| `archive/scripts/bash/generate_components.sh` | 36 | Archived shell script calls dead tarball script. Pre-commit excludes `archive/` so won't block. Leave as archived history or delete the line — user's call |
| `resources/deconstructor_output/` | entire dir | Removed by `git submodule deinit` + `git rm` |

### Files that reference `deconstructor_output` but are NOT the submodule (live path — KEEP)

| File | Why it stays |
|------|-------------|
| `go_modules/tools/pth.go:121` | Go path constant → `go_modules/deconstructor/output/deconstructor_output.json` (live Go output) |
| `go_modules/deconstructor/data/matchdata.go:531` | Writes to Go output path |
| `go_modules/deconstructor/main.go:57,100` | Go output dir references |
| `scripts/build/deconstructor_output_add_to_db.py` | The live sync script (reads Go output) |
| `scripts/find/deconstruction_finder.py:27` | Reads Go output `matches.tsv` |
| `scripts/bash/generate_components.py:40` | Runs the live sync script |
| `tests/scripts/build/test_deconstructor_output_add_to_db.py` | Tests for live sync |
| `.github/workflows/draft_release.yml:116` | Runs live sync |
| `.github/workflows/mobile_release.yml:164` | Runs live sync |
| `.github/workflows/submodules_update.yml:122` | Runs live sync |
| `justfile:331` | Runs live sync |
| `tools/paths.py:284,287-288,729` | `go_deconstructor_output_dir` / `go_deconstructor_output_json` (live Go output paths) |

## Goal

Remove every reference to the premade submodule/tarball path so that
`go_modules/deconstructor/output/deconstructor_output.json` is the single source
of truth, and `resources/deconstructor_output` no longer exists in the repo.

## How we'll know it's done

- `git submodule status` shows no `resources/deconstructor_output` entry.
- `.gitmodules` has no deconstructor_output block.
- `rg --hidden "deconstructor_output" --glob '!kamma/**' --glob '!.git/**'`
  returns only `go_deconstructor_output_*` paths, the Go source references
  (`pth.go`, `matchdata.go`, `main.go`), and the `add_to_db` script/test.
- `uv run pytest tests/` passes.
- `uv run ruff check` and `uv run pyright` pass on all touched files.
- `git clone` of the repo + `contributor_setup.py` no longer fetches the
  submodule.

## Out of scope

- The `digitalpalidictionary/deconstructor_output` GitHub repo itself — leave it
  as an archive; just deinit the submodule from dpd-db.
- Any change to the Go deconstructor or `deconstructor_output_add_to_db.py`.
- The `tbw_deconstructor_js_path` in `paths.py` — that's BW2 javascript,
  unrelated to the submodule.
