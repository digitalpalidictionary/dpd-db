# Plan: Retire the `resources/deconstructor_output` submodule system

Read `spec.md` first. The carrier list there is the verified complete sweep.
This is a scoped deletion — no new logic, just removing dead surface area.

## Phase 1 — Remove the submodule

- [x] 1.1 `git submodule deinit -f resources/deconstructor_output`
- [x] 1.2 `git rm resources/deconstructor_output`
- [x] 1.3 Remove the `[submodule "resources/deconstructor_output"]` block from
      `.gitmodules`
- [x] 1.4 `rm -rf .git/modules/resources/deconstructor_output`
      → verify: `git submodule status` has no deconstructor_output entry

## Phase 2 — Delete dead scripts and paths

- [x] 2.1 Delete `scripts/build/tarball_deconstructor_output.py`
      → verify: file not found
- [x] 2.2 Remove from `tools/paths.py`:
      - `self.deconstructor_output_dir` (line ~306)
      - `self.deconstructor_output_json` (lines ~321-322)
      - `self.deconstructor_output_tar_path` (lines ~324-325)
      - the `# resources/deconstructor_output` comment (line ~320)
      - **KEEP** `go_deconstructor_output_dir` (line ~284), `go_deconstructor_output_json`
        (lines ~287-288), and `go_deconstructor_output_dir` in the mkdir loop (line ~729)
      → verify: `uv run pyright tools/paths.py` passes;
        `rg "deconstructor_output_(dir|json|tar_path)\b" tools/paths.py` only hits
        `go_deconstructor_output_*`
- [x] 2.3 Remove the dead `create_tarball` call site from `tools/tarballer.py`
      (lines ~109-112). **KEEP the `create_tarball` function** —
      `audio/db_create.py` calls it.
      → verify: `rg "create_tarball" audio/` still works;
        `uv run pyright tools/tarballer.py` passes

## Phase 3 — Remove references from lists

- [x] 3.1 Remove `"resources/deconstructor_output"` from `REQUIRED_SUBMODULES`
      in `scripts/onboarding/contributor_setup.py`
- [x] 3.2 Remove `"deconstructor_output"` from `ACTIVE_REPOS` in
      `scripts/project_management/project_health_check.py`
- [x] 3.3 Verify `scripts/bash/generate_components.py` has no tarball reference
      → verify: `rg "tarball_deconstructor" scripts/` returns nothing (excluding archive/)
- [x] 3.4 `archive/scripts/bash/generate_components.sh:36` — left as archived
      history (pre-commit excludes `archive/`). User's call; no edit made.

## Phase 4 — Sweep and verify

- [x] 4.1 Full sweep:
      `rg --hidden "deconstructor_output" --glob '!kamma/**' --glob '!.git/**'`
      → only `go_deconstructor_output_*` paths, Go source references
        (`pth.go`, `matchdata.go`, `main.go`), and `deconstructor_output_add_to_db.py`
        should remain
- [x] 4.2 `uv run pytest tests/` passes (no new failures)
- [x] 4.3 `uv run ruff check` on all touched files
- [x] 4.4 `uv run pyright` on all touched files
- [x] 4.5 `git clone` test (reasoned): contributor_setup no longer fetches
      the submodule — `resources/deconstructor_output` removed from `REQUIRED_SUBMODULES`

## Phase 5 — Finalize

- [x] 5.1 Review and finalize via kamma flow
- [ ] 5.2 Close issue #157 if this was the last open item
