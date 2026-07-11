# Spec: Stop makedict/printer leaving artifacts in the repo root

**Issue:** #157 (refactoring umbrella)
**Date:** 2026-07-11

## Problem

Two files accumulate in the repo root as side-effects of every build:

1. **`typescript`** — the four `makedict*` justfile recipes wrap the build in
   `script -q -c "…"` (to fake a TTY so ANSI colours survive into
   `ansi2html`), but never pass `script` an output file, so it writes its
   default transcript to `./typescript` on every run. It was papered over
   with a `.gitignore` entry instead of fixed.
2. **`dpd_operations.log`** — `tools/printer.py:223` hardwires
   `printer = Printer(Path("dpd_operations.log"))`, so every script that
   imports the printer appends TSV rows to the cwd. 14 MB, never rotated,
   never read by anything in the codebase.

The user wants no artifacts when a build finishes; the HTML files in `logs/`
are the only record needed.

## Decision (user-approved: option C)

1. **justfile:** give `script` a `/dev/null` transcript, and DRY the
   four copy-pasted `script | tee | ansi2html` pipelines into one hidden
   `_logged-makedict` recipe that the variants call. Behaviour otherwise
   preserved exactly (no `-e`/`pipefail` added — `makedict-quick`/`-all`
   rely on the reset step running even after a failed build).
   Accepted nuance: the variants moved from shebang-bash bodies to
   linewise recipes, so if a *leading config script* fails, `just` now
   stops before the build (fail-fast improvement). A failed *build*
   still exits 0, so the trailing config reset still runs — the case
   that matters is preserved.
1b. **scripts/cl wrappers (found in review):** `scripts/cl/dpd-makedict`
   and `scripts/cl/dpd-build-db` had the same bare `script -q -c` call
   and also wrote `./typescript`; both got the `/dev/null` transcript.
2. **tools/printer.py:** remove the dead TSV logging machinery
   (`TSVFormatter`, logger setup, `_log()` and all its call sites, the
   unused `line`/`session` attributes); singleton becomes `Printer()`.
   Console output and timing behaviour unchanged. Modernize type hints
   (`int | str`, drop `Optional`/`Union`).
3. **Cleanup:** delete stale `typescript` and `dpd_operations.log`;
   remove the now-unneeded `typescript` entry from `.gitignore`.
4. **Docs:** update the `Tools/printer.py` section in `CLAUDE.md`
   (drop the TSV-logging claims). `CLAUDE.md` is a symlink; the real
   target `AGENTS.md` was edited.
5. **Regression guard (added in review):** the two import-side-effect
   tests (`test_create_inflection_templates.py`,
   `test_families_to_json.py`) previously excused the printer's log file
   and only checked leftover *directories*; they now assert the cwd is
   left completely untouched (no files, no dirs).

Out of scope: the vendored printer copy in `resources/other-dictionaries`
(separate submodule repo).

## Verification

- `just --list` still shows the four makedict recipes, not the hidden one.
- Grep confirms no remaining references to `dpd_operations.log`,
  `TSVFormatter`, or `_log(` under project code (excluding resources/).
- `uv run ruff check`, `uv run ruff format`, `uv run pyright` clean on
  touched Python files.
- Full test suite passes.
- A real `just makedict` run leaving no root artifacts is user-verified
  (too slow to run here).
