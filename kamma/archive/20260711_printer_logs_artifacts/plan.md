# Plan: Stop makedict/printer leaving artifacts in the repo root

## Phase 1: Implementation

- [x] 1. justfile: add hidden `_logged-makedict` recipe (`script … /dev/null | tee >(ansi2html …)`) and point `makedict`, `makedict-quick`, `makedict-all`, `makedict-min` at it
      → verify: `just --list` shows the four variants, recipe bodies deduplicated ✓
- [x] 2. tools/printer.py: strip TSV logging (TSVFormatter, logger, `_log()` + call sites, `line`/`session` attrs), singleton `Printer()`, modern type hints
      → verify: ruff check + format + pyright clean; no `_log(` references remain ✓
- [x] 3. Delete stale `typescript` and `dpd_operations.log`; drop `typescript` line from `.gitignore`
      → verify: files gone, `.gitignore` no longer lists typescript ✓
- [x] 4. CLAUDE.md: update Tools/printer.py section (remove TSV logging docs)
      → verify: section matches new printer API ✓ (edited real target `AGENTS.md`; `CLAUDE.md` is a symlink to it)

## Phase 2: Verification

- [x] 5. Repo-wide grep: no references to `dpd_operations.log` / `TSVFormatter` outside resources/ ✓
- [x] 6. Full test suite: `uv run pytest tests/` — 1471 passed, 16 deselected ✓
      Bonus end-to-end proof: the test run imports `tools.printer` transitively and did NOT recreate `dpd_operations.log`

## Phase 3: Review fixes (from /kamma:3-review + coderabbit)

- [x] 7. coderabbit review — 0 findings
- [x] 8. Independent review finding 1 (major): `scripts/cl/dpd-makedict` and `scripts/cl/dpd-build-db` also wrote `./typescript` — added `/dev/null` transcript to both; repo-wide `rg 'script -q'` sweep confirms no bare invocations remain
- [x] 9. Finding 2 (minor): fail-fast nuance on leading config-script failure documented in spec.md (build-failure → reset path confirmed preserved)
- [x] 10. Finding 3 (nit): stale printer comments in two tests removed; tests strengthened to assert cwd completely untouched (files AND dirs) — permanent regression guard. 13 passed; ruff + pyright clean
- [x] 11. Finding 4 (nit): `makedict: just _logged-makedict` body form kept for uniformity with the set/reset variants — accepted as-is

## Remaining

- User to verify a real `just makedict` run leaves no root artifacts
- `/kamma:4-finalize`
