# Plan: scripts/ triage & refresh

**Thread:** 20260713_scripts_triage
**Spec:** `spec.md` in this folder
**Plan verified against disk + git + CI:** 2026-07-13 (second investigation pass — see "Corrections to the spec" below)

## User decisions (resolved 2026-07-13 — no open questions remain)

1. **`scripts/verse/`** — the 14 verse scripts listed in the spec DO NOT EXIST on disk; only
   git-ignored `__init__.py` shells and stale `__pycache__/` remain. **User decision: DELETE the
   entire leftover shell** (`scripts/verse/` including `_data/`, `tests/`, all pycache). See
   Phase 6.1.
2. **`scripts/fix/verb_finder.py`** — owned by the still-open sibling kamma thread
   `kamma/threads/20260512_verb_finder/`. **User decision: TRIAGE IT HERE in this thread.** Use
   that thread's `plan.md` as the design reference when reading the file; record in the verdict
   summary that this thread handled the file so the sibling thread can be wrapped up.

The whole plan is executable without further user input.

## Corrections to the spec (found in verification pass, 2026-07-13)

The spec was written from a first audit; a second pass against disk, git history, and CI found:

- **Ghost files** (in spec/plan but NOT on disk; only stale `.pyc` remains — remove from triage,
  clean pyc in Phase 7): `scripts/add/synonym_single.py`, `scripts/suttas/sc/sc.py`,
  `scripts/extractor/compile_abbreviations_other.py` (deliberately deleted by archived thread
  `kamma/archive/20260411_abbreviations_exporter`), and all of `scripts/verse/*.py` except
  `__init__.py` shells (verse handled by deletion in Phase 6.1 per user decision).
- **CI workflows are a major reference carrier the spec missed.** 14 scripts are executed by
  `.github/workflows/*.yml` (draft_release, mobile_release, test_pdf, submodules_update,
  test_deconstructor_ci, static). Several scripts that look dead by justfile/pyc signals
  (`version_print.py`, `dealbreakers.py`, `db_rebuild_from_tsv.py`, `config_github_release.py`,
  `docs_add_indexes.py`, `docs_update_css.py`) are release-critical via CI. Full map below.
- **The "4 hardcoded dpd.db paths" claim is mostly wrong.** Only ONE is a real fixable path
  (`scripts/bash/initial_build_db.py:13`). The rest are a comment, GitHub-release asset-name
  matches, and a tar member name — see Phase 4 rows for exact analysis. Do NOT blindly replace.
- **Wrong justfile recipe names in the spec.** Actual names: `find_comm` (not
  find-comm-not-in-decon), `an-remaining` (not pass2pre-an-counts), `variants-processor` (not
  variants-process), `pass2-exceptions` (not pass2exceptions), `cone` (not extract-cone), `decon`
  (not deconstructor-add-to-db). There is NO `sanskrit-root-families` recipe (that script is
  CI-only). Uposatha scripts run inside `makedict-all` / `makedict-min`, not standalone recipes.
- **File counts corrected:** `scripts/cl/` has 9 shell scripts + README (not 10).
  `scripts/suttas/cst/` has 23 `.py` files (15 kn files: kn1–kn6, kn9, kn10, kn12–kn18 — no kn7,
  kn8, kn11). `scripts/suttas/dpd/` has 14 `.py` files.
- `.github/workflows/draft_release.yml:231` and `mobile_release.yml:234` run
  `scripts/prepare_sources.py`, which does not exist at that path in this repo — probably runs in
  a different working-directory (submodule). Verify in Phase 7, do not "fix" blindly.

## Architecture Decisions

- **No pre-made verdicts.** Each file's fate is decided at its task, based on objective signals:
  pycache freshness, justfile references, **CI workflow references**, script purpose,
  hardcoded-path issues, and code inspection. The agent makes verdicts without asking the user to
  run each script — dead code is dead regardless of whether it still runs.
- **Verdict menu:** `keep` (as-is + standard freshen) · `freshen` (standard freshen only) ·
  `improve` (real logic/UX work, scoped at the row) · `archive` (move to `archive/scripts/`,
  remove stale refs) · `delete` (truly worthless) · `move to fixme` (needs redesign, parked with
  inline notes) — or any bespoke mix.
- **Ordering is motivational:** low-hanging fruit first; problem children (big files, live
  pipeline, sutta processors) later.
- **Pytest:** where a surviving file has importable pure logic, add a smoke test under
  `tests/scripts/...` mirroring the source path. Decided per row. Interactive DB-loop tools,
  one-shot analysis scripts, and justfile-recipe-endpoints typically don't warrant tests.
  Tests ALREADY EXIST for 11 scripts (see Reference maps) — never duplicate those.
- **Evidence preserved here:** "last run" = newest `__pycache__` `.pyc` mtime (snapshot
  2026-07-13, before any re-runs). "git" = last SUBSTANTIVE commit (repo-wide mechanical sweeps
  excluded — see sweep list below). **No `.pyc` ≠ unused** — direct `python file.py` runs leave
  no cache.
- **Touch a file = own its lint.** Every edited file must pass `ruff check`, `ruff format`,
  `pyright` before the task is done. Note: the pre-commit hook's `exclude:` covers
  `scripts/bash/` and `archive/` — still lint `scripts/bash/` files by convention, but archived
  files need no lint.

## Execution playbook (follow these exactly at each row)

### Verdict heuristics (apply in this order)
1. Referenced by CI workflow → **keep/freshen**, never archive.
2. Referenced by justfile recipe → **keep/freshen**, never archive without removing the recipe
   deliberately (and that requires a strong reason).
3. Imported by live code outside scripts/ (gui2, tests) → **keep/freshen**.
4. Imported by a sibling script that survives → must survive too (see internal import graph).
5. Warm `.pyc` (2026) OR substantive commit within ~4 months → lean **keep/freshen** (recurring
   manual tool).
6. Cold/no `.pyc` + no refs + last substantive commit ≥ ~1 year + one-shot purpose (a finder/fixer
   written for a specific completed audit) → lean **archive**.
7. When torn between freshen and archive for a read-only finder: archive. For a DB-writing fixer
   whose fix is provably complete (the data condition it repaired can't recur): archive. If the
   condition can recur: keep.

### Repo-wide sweep commits — NOT evidence of activity
If a file's only recent commits are these mechanical sweeps, treat it as untouched since before
the sweep: `#157 db, tools, scripts: route hardcoded paths...` (2026-06-15) · `#157 sweep:
encoding="utf-8"...` (2026-06-11) · `#157 tools: clean up and refactor tools/ folder`
(2026-07-12) · `printer: update function names to plain colours` (2026-03-13) · `chore: ruff
format` (2025-12-18) · `chore: fix ruff errors` (2026-03-03) · `encoding utf8` (2025-06-16) ·
`refactor terminal printing and logging` (2025-03-25) · `ruff check` (2025-02-24) · `DpdHeadword
DpdRoot` (2024-09-20) · `sort scripts` (2024-09-20). The `git:` field on each row below already
has sweeps filtered out; `git: none` means the file has ONLY ever had sweep/data-update commits.

### Standard freshen procedure (every surviving file)
1. Read the whole file.
2. Module docstring if missing (one or two sentences: what it does, when to run it). Function
   docstrings on non-trivial functions.
3. Modern type hints: `dict[str, str]`, `list[str]`, `tuple[str, str]`, `X | None` — never
   `Dict/List/Tuple/Optional`. Add hints where missing on function signatures.
4. `Path` from pathlib for all file paths, not `os.path`.
5. Bare `print()` → `tools.printer` (`from tools.printer import printer as pr`) where sensible.
   EXCEPTIONS: leave `print` in `scripts/tutorial/` (teaching material) and in scripts using
   `rich.print` deliberately.
5b. Every script gets a `pr.yellow_title(...)` at the top of `main()` if it doesn't have one
   (user decision 2026-07-13) — applies to every freshen, including freshen-then-archive.
6. Delete dead commented-out code. Rename params shadowing builtins (`id` → `id_`).
7. Never mutate ORM objects unless the script's purpose is to update the DB. No `sys.path` hacks.
8. Gate: `uv run ruff check --fix <file>` then `uv run ruff format <file>` then
   `uv run pyright <file>` — fix ALL reported errors including pre-existing ones, with real
   behaviour-preserving fixes, never `# noqa`.
9. If a test exists for the file (see map below): `uv run pytest tests/scripts/<mirrored path>`.
10. Do NOT run the script itself.

### Archive procedure
1. `mkdir -p archive/scripts/<subdir>` then `mv scripts/<subdir>/<file>.py archive/scripts/<subdir>/`
   (plain `mv` — NO git commands; user stages/commits at the end).
2. Read the file first and move its associated data files (JSON/TSV it reads or writes that live
   in scripts/) alongside it — check the data-file map below.
3. justfile recipe? Delete the recipe (verify the real name via `rg -n "<filename>" justfile`).
4. `tools/paths.py` entry? Remove the attribute — but first `rg -n "<attr_name>"` repo-wide to
   confirm nothing live uses it; if something live uses it, the script is NOT archivable.
5. Delete the file's `__pycache__/` entries: `rm scripts/<subdir>/__pycache__/<stem>.*.pyc`.
6. No lint needed on archived files (`archive/` is excluded from pre-commit).
7. Record one-line reason on the row.

### fixme procedure
1. `mkdir -p scripts/fixme` (first use), `mv` script + data files there.
2. Add a `# FIXME:` comment block at the very top of the file (below shebang/docstring): what the
   script is for, what's broken/incomplete, what a redesign needs.
3. Retarget (don't delete) any `tools/paths.py` entries to the new path.
4. Fixme files must still pass ruff+pyright (scripts/fixme/ is NOT hook-excluded).

## Reference maps (verified 2026-07-13 — re-verify with the given commands before relying on them)

### justfile recipes → scripts (verify: `rg -n "scripts/" justfile`)
| Recipe | Script |
|---|---|
| `initial_setup_run_once` | scripts/bash/initial_setup_run_once.py |
| `initial_build_db` | scripts/bash/initial_build_db.py |
| `generate_components` | scripts/bash/generate_components.py |
| `_logged-makedict` (used by makedict/-quick/-all/-min) | scripts/bash/makedict.py |
| `makedict-quick` | scripts/build/config_quick_profile.py (+ `reset` arg) |
| `makedict-all` | scripts/build/config_uposatha_day.py force · config_uposatha_reset.py force |
| `makedict-min` | scripts/build/config_uposatha_reset.py force |
| `initial_build_db_and_export_all` | scripts/bash/initial_build_db_and_export_all.py |
| `variants-processor` | scripts/find/variants_process.py |
| `pass2-exceptions` | scripts/fix/pass2exceptions.py |
| `find_comm` | scripts/find/comm_not_in_decon_finder.py |
| `an-remaining` | scripts/find/pass2pre_an_counts.py |
| `newsletter`, `newsletter-fresh` | scripts/build/newsletter_scraper.py (fresh also rm's newsletter_processed.json) |
| `cone` | scripts/extractor/extract_cone.py |
| `decon` | scripts/build/deconstructor_output_add_to_db.py |

### CI workflows → scripts (verify: `rg -n --hidden "scripts/" .github/`)
Referenced by draft_release / mobile_release / test_pdf / submodules_update /
test_deconstructor_ci unless noted:
- scripts/bash/initial_setup_run_once.py
- scripts/build/config_github_release.py · db_rebuild_from_tsv.py · root_has_verb_updater.py ·
  sanskrit_root_families_updater.py · families_to_json.py · deconstructor_output_add_to_db.py ·
  api_ca_eva_iti_iva_hi.py · ebt_counter.py · dealbreakers.py · zip_goldendict_mdict.py ·
  tarball_db.py · version_print.py (sets RELEASE_TAG — release-critical)
- scripts/build/docs_add_indexes.py · docs_update_css.py (static.yml, docs deploy)
- `scripts/prepare_sources.py` (draft_release:231, mobile_release:234) — path does not exist
  here; investigate in Phase 7.

### tools/paths.py entries pointing into scripts/ (lines ~613–637)
`scripts/build/newsletter_processed.json` · `scripts/extractor/extract_cone.tsv` ·
`scripts/extractor/extract_cpd.tsv` · `scripts/find/most_common_missing_words.tsv` ·
`scripts/fix/fix_synonym_entries.json` · `suttas_dpd_dir = scripts/suttas/dpd` ·
`scripts/suttas/vaggas/compile_vaggas.tsv`

### External importers of scripts/ modules
- `gui2/main.py` imports `scripts.onboarding.data_submission` (submit_data) and
  `scripts.onboarding.contributor_update` (update_environment) — onboarding is LIVE library code.
- `tests/scripts/build/` tests exist for: api_ca_eva_iti_iva_hi, deconstructor_output_add_to_db,
  ebt_counter, families_to_json, root_has_verb_updater, sanskrit_root_families_updater.
- `tests/scripts/onboarding/` tests exist for: contributor_setup, contributor_update,
  data_submission, desktop_shortcut, launch_gui.

### Internal import graph (a survivor's imports must survive)
- `scripts/suttas/vaggas/compile_vaggas.py` imports `scripts.add.vagga_codes.shared`
  (**cross-directory** — archiving vagga_codes breaks compile_vaggas).
- `vagga_codes/runner.py` imports vagga_codes an/kn/mn/sn + shared; an/kn/mn/sn/dhp_m2 import shared.
- `build/config_uposatha_reset.py` imports `build.config_uposatha_day`.
- `extract_cone.py` imports: _ai_extraction, _load_cone, _output, _pos_mapping, _prompts,
  _read_cone, _signal_handler, _word_list.
- `extract_cpd.py` imports: _ai_extraction, _output, _pos_mapping, _read_cpd, _signal_handler,
  _word_list (NOT _prompts, NOT _load_cpd).
- `_load_cone` → _read_cone; `_load_cpd` → _read_cpd (**_load_cpd is imported by nothing** — dead
  candidate); `_word_list` → _dpd_headwords + _tsv_helpers; `_read_cone`/`_read_cpd` → _normalize.
- `onboarding/contributor_setup.py` → desktop_shortcut; `contributor_update.py` → contributor_setup.
- cst: an/mn/sn/kn*/main → `cst.modules`; main → `cst.kn2`.
- sc: `main.py.py` → blurbs, links, modules, suttas; modules → natural_sort; blurbs/suttas → modules.

### Data files living in scripts/ (git-tracked unless noted)
- `scripts/build/newsletter_processed.json` (tracked, paths.py)
- `scripts/build/mkdocs_overrides/{main.html, partials/header.html}` (used by docs build)
- `scripts/fix/fix_synonym_entries.json` (tracked) · `scripts/fix/pass2exceptions.json` (gitignored)
- `scripts/extractor/extract_cone.tsv`, `extract_cpd.tsv` (gitignored, paths.py)
- `scripts/find/most_common_missing_words.tsv`, `most_common_missing_words_old.tsv` (gitignored)
- `scripts/suttas/**/*.tsv` (gitignored via `scripts/suttas/*/*.tsv`; the vaggas/ TSVs were
  force-added and ARE tracked). Strays to clean: `bjt/an.bak.tsv`, `cst/cst copy.tsv`,
  `dpd/kn8-thi.tsv` (no matching script — `kn9-thi.py` exists; check which TSV it writes).
- `scripts/cone/{dpd_operations.log, extraction.log}` — no code anywhere references scripts/cone/.

---

## Phase 1 — Root-level cleanup (quick wins)

> **Working mode (final, session 2): one script at a time, user decides, agent does nothing
> unopposed.** User says "next" → agent replies with ONLY: the `uv run <path>` command, a short
> description, and a recommendation — then stops. User gives the verdict and any go-ahead. Only
> then does the agent act, and only on what was agreed. Standard freshen (type hints, docstrings,
> obvious broken-logic fixes) is bundled into a keep-in-some-form go-ahead automatically; the
> verdict itself and the script's purpose/utility are always the user's call. See spec.md
> "Working mode" section for the full loop.
>
> **Concurrency marker (see spec.md ~line 150): mark a row `[~]` the moment you start step 2 on
> it — before presenting the recommendation, not after.** Multiple agents run against this same
> plan.md at once; `[~]` is the only signal that stops a collision. Re-read plan.md from disk
> immediately before editing it, since another agent may have written to it since your last read.
> Flip to `[x]` only once the user confirms the row is done.
>
> Session 1 (and the first minutes of session 2) got this backwards — the agent picked verdicts
> and executed them (archive session.py, delete cone/, edit cl/ wrapper + README) before any user
> input. All of that has been reverted except `scripts/cone/`'s two log files, which were
> untracked and are not recoverable (see row below). Every row is back to `[ ]`/TBD.

- [x] `scripts/session.py` → renamed `scripts/script_template.py` — user's deliberate reusable
  template for quickly iterating over the db, kept intentionally
  - user decision (2026-07-13, session 2): rename + freshen, keep as the go-to quick-start
    template (distinct purpose from `scripts/tutorial/db_search_example.py`, which is teaching
    material, not a working-scratchpad template)
  - freshen applied: renamed, module + function docstrings added, `main()` type-hinted
    (`-> None`), dropped unused `enumerate` counter, `ruff check --fix` + `ruff format` +
    `pyright` clean
  - → verify: `uv run ruff check scripts/script_template.py` clean; `uv run pyright
    scripts/script_template.py` clean; `rg -rn "scripts/session|scripts\.session"` finds no live
    references (only historical kamma docs, expected)

- [x] `scripts/cone/` — only 2 log files (`dpd_operations.log`, `extraction.log`), no Python
  - the 2 log files were deleted in error during session 2 before user sign-off (untracked,
    not recoverable from git)
  - user decision (2026-07-13, session 2): delete the folder — Cone extraction work now lives in
    the `resources/other-dictionaries/` submodule; this was a stale output dir from the old
    location
  - → verify: `scripts/cone/` confirmed absent from disk

- [x] `scripts/server/` — only `update-dpd.sh` (server management shell script), no Python
  - verdict: keep (user decision, 2026-07-13) — live dpdict.net deploy script, runs server-side
    via scp; bare `uv sync` is deliberate (server needs only specific groups, not dev groups)
  - user fixed the dead commented line (truncated `download_and_unzip_db.` filename) themselves
  - → verify: file untouched by agent; no repo references expected (server-side by design)

- [x] `scripts/cl/` — 9 shell wrappers (`dpd-anki`, `dpd-bhashini`, `dpd-build-db`, `dpd-example`,
  `dpd-gui`, `dpd-kill-webapp`, `dpd-makedict`, `dpd-sandhi`, `dpd-webapp`) + README.md
  - user decision (2026-07-13, session 2): delete — superseded by `just` commands. Note: only 5
    of 9 (`anki`, `build-db`→`initial_build_db`, `gui`, `makedict`, `webapp`) had a direct just
    recipe equivalent at delete time; `bhashini`, `example`, `kill-webapp`, `sandhi` did not
    (flagged to user before deleting; user confirmed delete anyway)
  - action taken: `rm -rf scripts/cl/` (all 9 wrappers + README); removed the
    `export PATH=".../scripts/cl:$PATH"` line from `~/.bashrc:123` (no separate `~/bin`
    symlinks existed — PATH pointed straight at the directory)
  - → verify: `scripts/cl/` absent from disk (confirmed); `~/.bashrc` no longer references
    `scripts/cl` (confirmed)

- [x] **Phase 1 wrap:** ruff+format+pyright on any touched files; stale dirs resolved
  - only Python file touched: `scripts/script_template.py` (already linted+formatted+pyright
    clean at its own row); `scripts/cl/` was bash (not lint-gated) and is deleted;
    `scripts/cone/` had no code and is deleted; `scripts/server/` untouched
  - → verify: `uv run ruff check scripts/script_template.py` → clean; `scripts/cone/` and
    `scripts/cl/` confirmed absent from disk

---

## Phase 2 — find/ + fix/ directories (49 files, one-shot tools)

One-shot analysis and data-repair tools. Expect mostly `archive` verdicts. Exceptions wired into
the justfile: `variants_process.py` (`variants-processor`), `comm_not_in_decon_finder.py`
(`find_comm`), `pass2pre_an_counts.py` (`an-remaining`), `pass2exceptions.py`
(`pass2-exceptions`). For DB-writing fixers, apply heuristic 7: archivable only if the repaired
condition can't recur.

### 2.1 — find/ directory (27 files, all read-only)

- [x] `scripts/find/1000_most_common_words.py` — 1000 most common words analysis
  - no pyc · refs: none · git: 2026-06-02 created ("scripts: 1000 most common words finder") — recent
  - verdict: archive (user decision, 2026-07-13) — one-shot export, moved to
    `archive/scripts/find/`; no pyc, no justfile/paths.py/README refs, no data files to move
  - → verify: file in `archive/scripts/find/`; `rg -n "1000_most_common" justfile tools/paths.py
    scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/books_with_most_missing_words_finder.py` (109 lines)
  - no pyc · refs: none · git: none (sweeps only since ≤2025-06)
  - verdict: archive (user decision, 2026-07-13) — one-shot "which book next for missing
    examples" planning aid; moved to `archive/scripts/find/`; no pyc/refs/data files
  - → verify: file in `archive/scripts/find/`; `rg -n "books_with_most_missing" justfile
    tools/paths.py scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/comm_not_in_decon_finder.py` (195 lines) — commentary words not in deconstructor
  - justfile `find_comm` · no pyc · git: 2026-02-26 "improve commentary words not in lookup table"
  - verdict: keep (user decision, 2026-07-13) + standard freshen
  - freshen applied: fixed `commentray_books` → `commentary_books` typo on `FinderData`; expanded
    module docstring (what + how to run); added docstrings to every function; `main() -> None`
    type hint; import order fixed (stdlib/third-party/local groups)
  - → verify: `uv run ruff check scripts/find/comm_not_in_decon_finder.py` clean; `uv run pyright
    scripts/find/comm_not_in_decon_finder.py` → 0 errors, 0 warnings

- [x] `scripts/find/compound_type_wrong.py` — find wrong compound types
  - no pyc · refs: none · git: 2026-03-29 created
  - verdict: keep + freshen (user decision, 2026-07-13)
  - freshen: fixed copy-pasted docstring (was the dupe-finder's), `main() -> None`,
    set comprehension, renamed loop var
  - → verify: ruff check + format + pyright clean ✓

- [x] `scripts/find/decon_errors_finder.py` — deconstructor error finder
  - no pyc · refs: none · git: 2025-05-29
  - verdict: keep + freshen + move (user decision, 2026-07-13) — it's a recurring db integrity
    check, moved to `db_tests/single/test_deconstructor_errors.py`
  - freshen: docstring rewritten, `is_valid_json` tuple-return replaced with
    `parse_deconstructions() -> list[str] | None`, `main() -> None`, typed error dict
  - → verify: ruff check + format + pyright clean ✓; no refs to old name anywhere ✓

- [x] `scripts/find/deconstruction_finder.py` — find missing deconstructions
  - no pyc · refs: none · git: none (sweeps only since ≤2025-06)
  - verdict: keep (user decision, 2026-07-13) — useful debugging tool, kept as-is behaviorally
  - freshen applied: expanded module docstring (what it does + how to use `find_me`), added
    docstrings to both functions, type-hinted both (`-> None`), removed 3 lines of dead
    commented-out alternative-match code
  - → verify: `uv run ruff check scripts/find/deconstruction_finder.py` clean; `uv run pyright
    scripts/find/deconstruction_finder.py` → 0 errors, 0 warnings

- [x] `scripts/find/dpd_code_vs_sc_code_difference_finder.py` — DPD vs SC code differences
  - no pyc · refs: none · git: 2026-02-09 created
  - verdict: archive (user decision, 2026-07-13) — one-shot DPD-vs-SC sutta-code alignment
    audit; moved to `archive/scripts/find/`; no pyc/refs/data files
  - → verify: file in `archive/scripts/find/`; `rg -n "dpd_code_vs_sc_code" justfile
    tools/paths.py scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/headings_finder.py` — headings TUI (interactive, pass2 workflow)
  - no pyc · refs: none · git: 2025-10-19 "#175 pass2: find headings tui"
  - verdict: freshen then archive (user decision, 2026-07-13) — froze the pass2-#175 workflow tool
    into its final documented state before retiring it
  - freshen applied: module docstring rewritten (what + workflow note), docstrings +
    type hints added to all 3 functions, ruff+format+pyright clean
  - archived to `archive/scripts/find/headings_finder.py`; no justfile/paths.py/README refs to
    remove; no pyc to clean (none existed)
  - → verify: file in `archive/scripts/find/`; `rg -n "headings_finder" justfile tools/paths.py
    scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/id_lemma_dupe_finder.py` — find duplicate id/lemma pairs
  - no pyc · refs: none · git: 2026-01-01 created
  - verdict: archive + fix root cause (user decision, 2026-07-13) — instead of keeping a dupe
    finder, `lemma_1` now has a real UNIQUE constraint in `db/models.py` (`unique=True`), making
    this script and `lemma_1_dupes.py` obsolete; the db enforces it on next rebuild
  - user fixed the two live dupes first (`hatthaka 3`, `nāsa 2.1`); note SQLite applies the
    constraint on rebuild (`db_rebuild_from_tsv` / `initial_build_db`), not to the current file
  - docs check: `docs/technical/dpd_headwords_table.md` already says "unique headword and
    number" — accurate, no edit needed
  - → verify: file in `archive/scripts/find/`; `uv run ruff check` + `pyright db/models.py`
    clean ✓; `rg -n "id_lemma_dupe" justfile tools/paths.py scripts/find/README.md` → 0 ✓

- [x] `scripts/find/lemma_1_dupes.py` — find duplicate lemma_1 entries
  - no pyc · refs: none · git: 2026-03-29 created
  - flagged before verdict: docstring claimed to check `id` too but only checked `lemma_1`; logic
    bug `if count == 2` missed words duplicated 3+ times (should be `count > 1`)
  - verdict: freshen then archive (user decision, 2026-07-13)
  - freshen applied: fixed docstring, fixed `count == 2` → `count > 1` bug, `main() -> None`,
    added function docstring, import order fixed, ruff+format+pyright clean
  - archived to `archive/scripts/find/lemma_1_dupes.py`; no justfile/paths.py/README refs to
    remove; no pyc to clean (none existed)
  - → verify: file in `archive/scripts/find/`; `rg -n "lemma_1_dupes" justfile tools/paths.py
    scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/low_hanging_fruit_finder.py` — low-hanging fruit TUI
  - no pyc · refs: none · git: 2025-10-27 "update the low-hanging fruit finder tui"
  - verdict: keep + freshen (user decision, 2026-07-13) — user asked whether it belongs in
    `scripts/add/` instead; agent disagreed (it's read-only, never writes to the DB — fits
    `find/`'s pattern, not `add/`'s DB-writing pattern) and user accepted keeping it in `find/`
  - freshen applied: expanded module docstring (what + how to use), `main() -> None`, dropped
    unused `index` loop var from `enumerate`
  - → verify: `uv run ruff check scripts/find/low_hanging_fruit_finder.py` clean; `uv run pyright
    scripts/find/low_hanging_fruit_finder.py` → 0 errors, 0 warnings

- [x] `scripts/find/missing_meanings.py` — find entries missing meanings
  - no pyc · refs: none · git: none substantive (last touch was 2026-07-12 tools-refactor sweep) ·
    freshened + had real bugs fixed 2 days ago in `kamma/archive/20260711_tools_cleanup`
  - verdict: keep as library (user decision, 2026-07-13) — useless as a standalone CLI, but the
    user wants `find_missing_meanings()` wired into gui2 as a post-save dialog on pass2's
    existing-word update flow, letting missing example/commentary words be queued as new-word
    candidates. Spun off to its own thread rather than scoped here:
    `kamma/threads/20260713_missing_meanings_dialog/` (spec + plan written). This file itself is
    untouched by this triage thread; its integration is tracked in that sibling thread.
  - → verify: `kamma/threads/20260713_missing_meanings_dialog/spec.md` and `plan.md` exist

- [x] `scripts/find/most_common_missing_word_finder.py` → renamed
  `scripts/find/most_common_missing_word_1_finder.py`
  - pyc 2025-10-30 · writes `scripts/find/most_common_missing_words.tsv` (gitignored, has
    `tools/paths.py` entry) · git: 2025-11-02 (#176)
  - verdict: keep + freshen + rename (user decision, 2026-07-13) — kept as a live recurring
    workflow (README-documented, `paths.py`-tracked), renumbered `_1_` to make the
    generate→report pairing with `_2_analysis` explicit
  - freshen applied: fixed nonsensical type hint `dict[dict[str,int], dict[str,set[str]]]` on
    `group_similar_words`/`sort_groups` (dict keys can't be dicts) → added a `WordGroup`
    TypedDict and used it correctly throughout; removed 2 lines of dead commented-out code
    (`# and not book.endswith("a")`, `# return ["kn15", "kn16"]`); added missing type hints +
    docstrings to every function; module docstring expanded to note the `_2_analysis` pairing
  - `tools/paths.py` unaffected (its `most_common_missing_words_tsv_path` entry points at the
    output TSV, not the script filename)
  - updated `scripts/find/README.md` (2 references) to the new filename
  - → verify: `uv run ruff check` + `uv run pyright
    scripts/find/most_common_missing_word_1_finder.py` clean; `rg -n
    "most_common_missing_word_finder"` (old name) → 0 matches outside kamma docs

- [x] `scripts/find/most_common_missing_word_analysis.py` → renamed
  `scripts/find/most_common_missing_word_2_analysis.py`
  - no pyc · refs: none · git: 2025-11-02 "#176 limit to dhamma & vinaya commentaries"
  - verdict: keep + freshen + rename (user decision, 2026-07-13) — companion report script for
    `_1_finder`'s output; user confirmed keeping them as two separate scripts (finder is an
    expensive corpus scan, analysis is a cheap re-runnable report — merging would force a full
    rescan just to re-check coverage stats)
  - freshen applied: fixed a real inconsistency — `open_file()` hardcoded the TSV path as a raw
    string while the finder used `pth.most_common_missing_words_tsv_path`; now routes through
    `ProjectPaths` too (the `_old.tsv` fallback stays a literal — it's a deprecated backup with
    no `paths.py` entry); added module docstring, function docstrings, type hints throughout
  - updated `scripts/find/README.md` to add this script to the Interface list (it was missing
    entirely, even before the rename)
  - → verify: `uv run ruff check` + `uv run pyright
    scripts/find/most_common_missing_word_2_analysis.py` clean; `rg -n
    "most_common_missing_word_analysis"` (old name) → 0 matches outside kamma docs

- [x] `scripts/find/origin_finder.py` — find word origins
  - no pyc · refs: none · git: none (sweeps only, ever)
  - verdict: archive (user decision, 2026-07-13) — distinct-value lister for `origin`, redundant
    with `test_allowable_characters.py`'s origins allowlist; moved to `archive/scripts/find/`
  - → verify: file in `archive/scripts/find/`; `rg -n "origin_finder" justfile tools/paths.py
    scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/pass2pre_an_counts.py` (146 lines) — remaining-words-in-AN counts
  - justfile `an-remaining` · no pyc · git: 2026-07-05 created — hot, active pass2 workflow
  - verdict: keep, no freshen needed (user decision, 2026-07-13) — already has full module +
    function docstrings, modern type hints, `Path`/`tools.printer` used correctly, no dead code
  - → verify: `uv run ruff check scripts/find/pass2pre_an_counts.py` clean; `uv run ruff format
    --check` → already formatted; `uv run pyright` → 0 errors, 0 warnings

- [x] `scripts/find/phonetic_var_most_common.py` — most common phonetic variants
  - no pyc · refs: none · git: 2026-05-31 created
  - a parallel agent moved the file to `archive/scripts/find/` mid-triage before this row was
    claimed here — collision, corrected: user's actual verdict was freshen-then-archive (not
    plain archive)
  - freshen applied on the archived copy: docstring clarified, magic number `20` → `TOP_N`
    constant, `main() -> None`, dropped unused `counted` var (F841), removed dead commented-out
    line, `enumerate` replaces manual index into `ordered`
  - → verify: file present at `archive/scripts/find/phonetic_var_most_common.py`; no lint gate
    required (archive/ is pre-commit-excluded) but freshened anyway per user request
  - → verify: TBD

- [x] `scripts/find/preposition_finder.py` — find preposition patterns
  - no pyc · refs: none · git: none (sweeps only since 2024)
  - verdict: freshen + archive (user decision, 2026-07-13) — freshened first (pr.tic/
    yellow_title/toc added, `main() -> None`, import order, simplified Counter/len checks),
    then moved to `archive/scripts/find/`
  - → verify: file in `archive/scripts/find/`; `rg -n "preposition_finder" justfile
    tools/paths.py scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/root_verb_finder.py` — find root verbs
  - no pyc · refs: none · git: 2025-03-10
  - note: distinct from `scripts/fix/verb_finder.py` (blocked row) — do not confuse
  - verdict: freshen then archive (user decision, 2026-07-13)
  - freshen applied: module + function docstrings, `main() -> None`, import order fixed
    (stdlib/third-party/local groups), ruff+format+pyright clean
  - archived to `archive/scripts/find/root_verb_finder.py`; no justfile/paths.py/README refs to
    remove; no pyc to clean (none existed)
  - → verify: file in `archive/scripts/find/`; `rg -n "root_verb_finder" justfile tools/paths.py
    scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/sanskrit_root_families_counter.py`
  - no pyc · refs: none · git: 2025-05-29
  - note: distinct from `scripts/build/sanskrit_root_families_updater.py` (CI-critical) — do not confuse
  - verdict: keep + freshen (user decision, 2026-07-13) — active resumable manual data-entry aid;
    trailing `# upto √ñā 553` comment is a genuine progress bookmark, preserved as-is (not dead
    code)
  - freshen applied: module docstring rewritten (what + how to use), `main() -> None`, dropped
    unused `enumerate` counter, renamed `counter` (the `Counter` instance) →
    `root_family_counter` to stop it shadowing the earlier loop variable name
  - → verify: `uv run ruff check scripts/find/sanskrit_root_families_counter.py` clean; `uv run
    pyright scripts/find/sanskrit_root_families_counter.py` → 0 errors, 0 warnings

- [x] `scripts/find/sinhala_sanna.py` — Sinhala sanna finder
  - no pyc · refs: none · git: none (sweeps only since ≤2025-06)
  - verdict: freshen + archive (user decision, 2026-07-13) — one-shot BJT sanna word-list
    export; freshened (module/function docstrings, type hints, dropped redundant `Path()`
    wraps, import order), moved to `archive/scripts/find/`
  - paths.py note: `bjt_sinhala_dir`/`bjt_dir` NOT removed — still used by
    `scripts/build/transliterate_bjt.py` (Phase 4 row)
  - → verify: file in `archive/scripts/find/`; `rg -n "sinhala_sanna" justfile tools/paths.py
    scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/sn_samyutta_mismatch_finder.py`
  - pyc 2026-04-20 · git: 2026-04-20 (#192 vagga work)
  - verdict: freshen then archive (user decision, 2026-07-13) — SN family_set/meaning
    cross-field integrity check from #192; the archived `20260419_vagga_sutta_codes` thread
    already ran it to 0 mismatches across 2258 SN headwords, so the condition it checks was
    fixed at the time; no live refs
  - freshen applied: added `pr.yellow_title()` at top of `main()` per the new standard-freshen
    convention (spec.md), converted final 2 `print()` calls to `pr.summary()`, tightened
    `rows: list[dict]` → `list[dict[str, str | int]]`
  - archived to `archive/scripts/find/sn_samyutta_mismatch_finder.py`; no justfile/paths.py/
    README refs to remove; found + removed the stale compiled
    `scripts/find/__pycache__/sn_samyutta_mismatch_finder.cpython-313.pyc` (a `.pyc` is a
    separate compiled artifact from the `.py` — `mv` doesn't take it with the source file)
  - → verify: `uv run ruff check` + `uv run pyright
    scripts/find/sn_samyutta_mismatch_finder.py` clean (pre-archive); file now in
    `archive/scripts/find/`; `rg -n "sn_samyutta_mismatch_finder"` → 0 matches outside kamma
    archive docs

- [x] `scripts/find/subheadings_finder.py` (156 lines)
  - no pyc · refs: none · git: none (sweeps only since ≤2025-06)
  - verdict: freshen then archive (user decision, 2026-07-13) — DB-writing fixer whose
    `db_session.commit()` was already commented out (never persisted its own change as
    written); targets a static CST-corpus condition that can't recur once actually applied
  - freshen applied: proper module docstring (what + how, flags the disabled commit), type hints
    on `__init__`/all methods (`-> None`, `make_soup`/`make_subheadings` params typed), `list[str]`
    on `mula_books`
  - archived to `archive/scripts/find/subheadings_finder.py`; no justfile/paths.py/README refs to
    remove; no pyc to clean (none existed)
  - → verify: file in `archive/scripts/find/`; `rg -n "subheadings_finder" justfile tools/paths.py
    scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/text_finder.py` — text search finder
  - no pyc · refs: none · git: none (sweeps only since 2024)
  - verdict: freshen + archive (user decision, 2026-07-13) — throwaway CST word-set scratchpad;
    freshened (module docstring moved to top, `pr.yellow_title`, `main() -> None`, dead
    commented filter removed, import order), moved to `archive/scripts/find/`
  - → verify: file in `archive/scripts/find/`; `rg -n "text_finder" justfile tools/paths.py
    scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/variant_dedupe.py` (124 lines)
  - no pyc · refs: none · git: 2026-05-09 (#144 variant dedupe work)
  - verdict: archive (user decision, 2026-07-13 — overriding agent's keep recommendation) — user
    confirmed this was a once-off cleanup for #144, not a recurring audit; already well-built
    (dry-run default, `--apply`/`--limit`/`--all`, confirmation prompt) so no freshen needed
    before archiving
  - archived to `archive/scripts/find/variant_dedupe.py`; no justfile/paths.py/README refs to
    remove; no pyc to clean (none existed)
  - → verify: file in `archive/scripts/find/`; `rg -n "variant_dedupe" justfile tools/paths.py
    scripts/find/README.md` → 0 matches ✓

- [x] `scripts/find/variants_process.py` (411 lines — largest finder)
  - justfile `variants-processor` · no pyc · git: 2026-04-28 (#144)
  - verdict: keep + bug fix (user decision, 2026-07-13) — user spotted that classifying a
    variant (p/t/s) did NOT remove it from `variant`; local `_assign` contradicted the
    canonical `tools/synonym_variant.py:assign_relationship` (var.add instead of var.discard,
    missing exclusivity discards, ASCII sort instead of pali_list_sorter)
  - fix: deleted local `_assign`/`_remove_from_variant`, now delegates to
    `assign_relationship` (incl. "delete" for the d key); ~55 duplicated lines gone
  - NOTE: db rows classified by earlier runs of the buggy logic may still hold classified
    words in `variant` — one-shot cleanup offered to user, pending their call
  - → verify: ruff check + format + pyright clean ✓; justfile `variants-processor` intact

- [x] `scripts/find/word_without_examples_analyser.py`
  - no pyc · refs: none · git: none (sweeps only, ever) · was listed in `scripts/find/README.md`
    (missed by the earlier "refs: none" signal — README refs aren't `rg`-visible in a `justfile`/
    `paths.py`-only sweep)
  - verdict: freshen then archive (user decision, 2026-07-13)
  - freshen applied: fixed copy-pasted docstring (was the generic "quick starter template" blurb),
    `main() -> None`, dropped unused `enumerate` counter
  - archived to `archive/scripts/find/word_without_examples_analyser.py`; removed its line from
    `scripts/find/README.md`; no justfile/paths.py refs; no pyc to clean (none existed)
  - → verify: file in `archive/scripts/find/`; `rg -n "word_without_examples_analyser" justfile
    tools/paths.py scripts/find/README.md` → 0 matches ✓

### 2.2 — fix/ directory (22 files; all write DB unless noted)

- [x] `scripts/fix/character_replacer.py`
  - no pyc · refs: none · git: none (sweeps only since 2024)
  - verdict: keep (user decision, 2026-07-13) — reusable find/replace-in-a-column template,
    same category as `scripts/script_template.py`
  - freshen applied: module docstring expanded (what + how to use the 3 constants), added
    `pr.yellow_title()` at top of `main()` per the standard-freshen convention, `main() -> None`,
    added function docstring, ruff+format+pyright clean
  - → verify: `uv run ruff check scripts/fix/character_replacer.py` clean; `uv run pyright
    scripts/fix/character_replacer.py` → 0 errors, 0 warnings

- [x] `scripts/fix/double_consonant_replacer.py` (73 lines)
  - no pyc · refs: none · git: 2026-05-28 "fix double_consonants replacer for -x-x → -xx cleanup"
  - verdict: convert to db_tests/single test (user decision, 2026-07-13 — overriding agent's
    initial "keep as fix script" recommendation). User's read: the -x-x typo class it targeted has
    already been fully eliminated by this script's prior run(s); its lasting value now is as a
    regression guard, same reclassification pattern as `decon_errors_finder.py` earlier in this
    thread. Auto-fix-with-commit capability dropped — future hits should be corrected via gui2,
    not blind auto-replace.
  - moved to `db_tests/single/test_double_consonant.py`; rewritten read-only using the
    `tools.printer` standard db_tests flow (`pr.yellow_title` → `pr.green_tmr`/`pr.yes` around the
    db load → `pr.green_title` → `pr.red` per hit → `pr.summary`/`pr.toc`), modeled on
    `test_deconstructor_errors.py`
  - original `scripts/fix/double_consonant_replacer.py` deleted; no justfile/paths.py/README refs;
    no pyc to clean (none existed)
  - → verify: `uv run ruff check db_tests/single/test_double_consonant.py` clean; `uv run pyright`
    → 0 errors, 0 warnings; ran live against `dpd.db` → 0 errors found (confirms the class really
    is eliminated); `rg -n "double_consonant_replacer" justfile tools/paths.py scripts/fix/` → 0
    matches ✓

- [x] `scripts/fix/example_1_2_cleaner.py`
  - no pyc · refs: `scripts/fix/README.md:22` · git: last substantive 2026-01-22 "#162 gui2: buttons
    for cleaning examples"
  - verdict: **keep + freshened**
  - fixes: removed dead `tools.sandhi_contraction` import (module deleted); updated `clean_example`
    call to new `SpeechMarkManager` signature; fixed wrong copy-paste docstring; added type hints
  - → verify: `uv run scripts/fix/example_1_2_cleaner.py` runs clean ✓

- [x] `scripts/fix/extra_brackets_remover.py`
  - no pyc · refs: none · git: 2025-10-30 "ignore brackets at start"
  - verdict: keep + freshen (user decision, 2026-07-13) — recurring meaning_1 typo class (any new
    contributor-written meaning can reintroduce repeated bracket annotations), kept as a manual
    fix script rather than reclassified to db_tests/single
  - freshen applied: **safety fix** — added the y/n commit-confirmation gate (previously
    committed unconditionally with no dry-run option, unlike `double_consonant_replacer.py`'s
    pattern); rewrote `print()` → `rich.print` with color-coded diff output matching that same
    script's style; module + function docstrings; `main() -> None`
  - → verify: `uv run ruff check scripts/fix/extra_brackets_remover.py` clean; `uv run pyright` →
    0 errors, 0 warnings

- [x] `scripts/fix/family_compound_and_idiom_update.py`
  - no pyc · refs: none · git: 2025-07-03 (MN sutta-name standardization run)
  - verdict: keep + freshen (user decision, 2026-07-13) — reusable hardcoded-constants rename
    tool, edited per rename job; kept over archive recommendation
  - freshen: `main() -> None`, `pr.yellow_title` replaces bare rich print, updated docstring
  - → verify: ruff check + format + pyright clean ✓

- [x] `scripts/fix/family_root_rename.py`
  - no pyc · refs: none · git: none (sweeps only since 2024)
  - verdict: keep + freshen (user decision, 2026-07-13)
  - freshen: expanded docstring, `main() -> None`, `rich.print` → `pr.green`, added `db_session.close()`
  - → verify: ruff check + format + pyright clean ✓

- [x] `scripts/fix/family_set_update.py`
  - no pyc · refs: none · git: none (sweeps only since 2024)
  - flagged before verdict: `db_session.commit()` was unconditional, no confirmation prompt
    (unlike `character_replacer.py`'s y/n gate) — worth noting since it looks like a reusable
    template but isn't
  - data check: queried live `dpd.db` directly — 0 rows have lowercase `nipāta` left in
    `family_set`; only capitalized `Nipāta` remains as part of book-title references ("Sutta
    Nipāta"), which the script's case-sensitive regex doesn't touch — the rename this script did
    is fully complete and can't recur (categorical relabeling, not an ongoing pattern)
  - verdict: archive (user decision, 2026-07-13), no freshen requested — one-off, job done
  - archived to `archive/scripts/fix/family_set_update.py`; no justfile/paths.py/README refs to
    remove; no pyc to clean (none existed)
  - → verify: file in `archive/scripts/fix/`; `rg -n "family_set_update" justfile tools/paths.py
    scripts/fix/README.md` → 0 matches ✓

- [x] `scripts/fix/family_word_remover.py`
  - no pyc · refs: none · git: none (sweeps only, ever)
  - verdict: archive (user decision, 2026-07-13) — hardcoded one-time family_word blank-out
    for 11 lemmas, condition provably complete; moved to `archive/scripts/fix/`
  - → verify: file in `archive/scripts/fix/`; `rg -n "family_word_remover" justfile
    tools/paths.py scripts/fix/README.md` → 0 matches ✓

- [x] `scripts/fix/family_word_update.py`
  - no pyc · refs: none · git: none (sweeps only since 2024)
  - verdict: keep + freshen (user decision, 2026-07-13 — overriding agent's archive
    recommendation) — kept as a reusable hand-edit-the-constants rename template for future
    family_word renames, not just the one-time makuṭa/makula case
  - freshen applied: **safety fix** — added y/n commit-confirmation gate (previously committed
    unconditionally); `find`/`replace` → `FIND`/`REPLACE` (module-level constants convention);
    `print("[bright_yellow]...")` → `pr.yellow_title()`; module docstring explains the
    edit-then-run workflow; `main() -> None`
  - → verify: `uv run ruff check scripts/fix/family_word_update.py` clean; `uv run pyright` → 0
    errors, 0 warnings

- [x] `scripts/fix/fix_synonym_entries.py` (201 lines)
  - no pyc · data: `fix_synonym_entries.json` (tracked, `tools/paths.py` entry) ·
    git: 2026-03-13 "#219 move to scripts/fix, add 2-pass detection and known fixes"
  - **concurrent-session conflict, resolved 2026-07-13:** two parallel agents reached opposite
    verdicts on this row at nearly the same time. This agent replicated the script's own
    detection logic against the live `dpd.db` (read-only, via `get_db_session`) and found it is
    NOT done — 15/428/783 corrupted (concatenated) entries and 66/178/300 non-headword entries
    still flagged across synonym/antonym/variant respectively — and recommended **keep**. The
    other agent, working the same row independently, recorded **archive** ("unclear purpose,
    days are done") and had already moved the file + JSON + removed the `paths.py` entry before
    this was noticed. User was told about the direct contradiction and the live-data numbers,
    and explicitly chose to keep the archive decision rather than restore it.
  - verdict: archive (user decision 2026-07-13, confirmed after being shown the conflicting
    live-data finding above)
  - archived: moved script + JSON to `archive/scripts/fix/`; removed `fix_synonym_entries_json_path`
    (and now-empty `# scripts/fix` comment) from `tools/paths.py`; no justfile recipe existed;
    cleaned stale `.pyc`
  - → verify: ruff check + format + pyright clean on `tools/paths.py` ✓ (archived file needs no lint)

- [x] `scripts/fix/gatha_cleaner.py`
  - no pyc · refs: none · git: none substantive (last touch 2026-07-12 tools sweep)
  - verdict: archive (user decision, 2026-07-13) — superseded: `clean_gatha()` is now live in
    `tools/cst_source/text_utils.py`, called by `tools/cst_source/examples.py` during CST
    extraction, so new example_2 gathā formatting is correct at source; this was a one-off
    retroactive db fix; moved to `archive/scripts/fix/`
  - → verify: file in `archive/scripts/fix/`; `rg -n "gatha_cleaner" justfile tools/paths.py
    scripts/fix/README.md` → 0 matches ✓

- [x] `scripts/fix/gitignore_cleaner.py` (119 lines, no DB) → moved + renamed folder
  - no pyc · refs: none · git: 2026-01-08 "keeping .DS_Store in .gitignore"
  - verdict: keep + freshen + move (user decision, 2026-07-13) — repo-hygiene tool, not DB/corpus
    related like `scripts/info/`; doesn't belong in `fix/` (no DB write) or `find/`. Moved to a
    new `scripts/repo_maintenance/` directory (new category, first file in it). User asked
    explicitly: keep report-only, no interactive auto-delete of gitignore lines — several flagged
    patterns are legitimate but simply not yet triggered this session (files a build/export step
    generates), so pruning needs a human per-line judgment call, not automation.
  - freshen applied: module docstring rewritten to state the report-only/no-auto-edit design
    intent; stripped leftover "thinking out loud" comments; `pr.tic()`/`pr.yellow_title()`/
    `pr.toc()` wrapping added (matching other scripts' `tools.printer` convention) while keeping
    `rich.Console`/`Table` for the actual report body (no printer equivalent for tables); narrowed
    bare `except Exception` → `except GitIgnorePatternError` (the actual exception type pathspec
    raises, confirmed via `pathspec.patterns.gitignore.GitIgnorePatternError`); dropped unused
    `original_line` variable; `all_paths` build simplified with `any()` for the match check
  - → verify: moved to `scripts/repo_maintenance/gitignore_cleaner.py`; old path removed, no
    justfile/paths.py/README refs, no pyc to clean; `uv run ruff check
    scripts/repo_maintenance/gitignore_cleaner.py` clean; `uv run pyright` → 0 errors, 0 warnings;
    ran live — same 22 unused patterns reported as the pre-freshen run (behavior preserved)

- [x] `scripts/fix/meaning_lit_fixer.py`
  - no pyc · refs: none · git: 2025-05-04 (gui2 improvements batch)
  - verdict: archive (user decision, 2026-07-13)
  - archived to `archive/scripts/fix/meaning_lit_fixer.py`; no justfile/paths.py/README refs to remove; no pyc to clean
  - → verify: file in `archive/scripts/fix/` ✓

- [x] `scripts/fix/nir_add_to_family_compound.py`
  - no pyc · refs: none · git: 2026-01-31 created ("add nir to family compounds" — one-shot, done)
  - verdict: **archived** — completed one-shot (only 2 rows remain, lexicographic judgment
    better handled per-word in gui2); commit was commented out, no main(), unused inspect import
  - → verify: moved to `scripts/fix/archive/` ✓

- [x] `scripts/fix/null_remover.py`
  - no pyc · refs: `scripts/fix/README.md:21` · git: none (sweeps only since 2024)
  - verdict: archive (user decision, 2026-07-13) — read-only NULL audit, condition likely fixed long ago
  - archived to `archive/scripts/fix/null_remover.py`; removed README reference; no justfile/paths.py refs; no pyc to clean
  - → verify: file in `archive/scripts/fix/`; `rg -n "null_remover" justfile tools/paths.py scripts/fix/README.md` → 0 matches ✓

- [x] `scripts/fix/pass2exceptions.py` (270 lines) → `archive/scripts/fix/pass2exceptions.py`
  - justfile `pass2-exceptions` · pyc 2026-06-27 · data: `pass2exceptions.json` (gitignored) ·
    git: 2026-06-27 "add pass2exceptions audit" — hot, actively used
  - **COLLISION NOTE:** a parallel agent freshened this file in place (added `Session`/`Iterator`
    type hints to `chunk`, `get_word_to_ids`, `get_headword_infos`, `analyse`, `run_tui`) and
    marked this row `[x]` with verdict "keep" before this correction. The user then explicitly
    told THIS session to archive it ("its too much work") — overriding that keep verdict. The
    freshening work is not lost: the archived copy already includes those type hints (the `mv`
    captured current disk content). Final verdict is archive, overriding "keep".
  - verdict: archive (user decision, 2026-07-13, given directly in this session) — the manual TUI
    review workflow itself was judged too labor-intensive to keep using, despite being a recently
    active, well-built tool. This is a deliberate behavior-preservation exception per the
    Architecture Decisions rule ("never archive a justfile-referenced script without removing the
    recipe deliberately, requiring a strong reason") — "too much work" is that strong reason.
  - archived to `archive/scripts/fix/pass2exceptions.py` + its own `pass2exceptions.json` tracking
    file (the "kept words" list colocated in `scripts/fix/`, distinct from gui2's live
    `pass2_exceptions.json` under `gui2/data/`, which is untouched); removed the `pass2-exceptions`
    justfile recipe (+ its `pass2` alias); removed stale pyc
  - → verify: file + json in `archive/scripts/fix/`; `rg -n "pass2-exceptions|pass2exceptions.py"
    justfile` → 0 matches; `just --list | grep pass2` → 0 matches; gui2's own
    `gui2/data/pass2_exceptions.json` confirmed untouched

- [x] `scripts/fix/root_sign_plus_remover.py`
  - no pyc · refs: none · git: 2025-11-02 created (one-shot `+` removal — likely done)
  - verdict: archive (user decision, 2026-07-13) — verified live db: 0 rows have `+` in
    `root_sign`, condition provably complete; `test_allowable_characters.py` still permits
    `+` in root_sign generally (no conflict); moved to `archive/scripts/fix/`
  - → verify: file in `archive/scripts/fix/`; `rg -n "root_sign_plus_remover" justfile
    tools/paths.py scripts/fix/README.md` → 0 matches ✓

- [x] `scripts/fix/sandhi_contraction_find_replace.py` (239 lines)
  - no pyc · refs: none · git: none (sweeps only since 2024)
  - verdict: archive (user decision, 2026-07-13) — functionality built into gui2 now
  - archived to `archive/scripts/fix/sandhi_contraction_find_replace.py`; no justfile/paths.py/README refs to remove; no pyc to clean
  - → verify: file in `archive/scripts/fix/`; `rg -n "sandhi_contraction_find_replace" justfile tools/paths.py scripts/fix/README.md` → 0 matches ✓

- [x] `scripts/fix/sanskrit_sutra_bsk.py`
  - no pyc · refs: none · git: 2026-06-07 created (one-shot sūtra (bsk) fix)
  - verdict: archive (user decision 2026-07-13 — cold one-shot fixer,
    `db_session.commit()` commented out, fix already applied)
  - archived: moved to `archive/scripts/fix/`; cleaned stale `.pyc`; no refs/justfile to update;
    file was already lint-clean (ruff+format+pyright)
  - → verify: n/a (no refs to update)

- [x] `scripts/fix/sn_set_updater.py`
  - no pyc · refs: none · git: 2025-11-21 (#56 sutta table work)
  - verdict: archive (user decision, 2026-07-13) — verified live db: 0 rows with the old
    `family_set` label, condition provably complete; moved to `archive/scripts/fix/`
  - → verify: file in `archive/scripts/fix/`; `rg -n "sn_set_updater" justfile tools/paths.py
    scripts/fix/README.md` → 0 matches ✓

- [x] `scripts/fix/variant_cleaner.py` (102 lines)
  - no pyc · refs: none · git: 2026-05-04 (#144 classify and clean variants)
  - verdict: **keep + freshened** — read-only variant data-quality audit; rewrote docstring with
    per-check explanation and usage; added `main()` function
  - → verify: `uv run scripts/fix/variant_cleaner.py` runs clean ✓

- [x] `scripts/fix/verb_finder.py` (478 lines) — verb finder (largest fixer)
  - no pyc · refs: none · git: 2026-05-22 "verb finder 1" · **user decision: triage here**,
    superseding open thread `kamma/threads/20260512_verb_finder/`
  - verdict: keep + freshen (user decision 2026-07-13) — read-only exploratory diagnostic,
    already well-structured (modern type hints, dataclasses, self-tests, pr.tic/toc). No DB
    writes. Data it checks (grammar field consistency) changes as entries are edited so the
    diagnostic remains useful. No refs/justfile/test needed.
  - freshen: replaced `pr.green_title("verb_finder (exploratory)")` with
    `pr.yellow_title("verb finder")` at top of `main()` per the standard-freshen convention
  - → verify: ruff check ✓ + format ✓ + pyright ✓ on `scripts/fix/verb_finder.py`

- [ ] **Phase 2 wrap:** ruff+format+pyright clean on all kept find/+fix/ files; justfile recipes
  intact; archived files in `archive/scripts/find/` and `archive/scripts/fix/` with data files
  - → verify: `uv run ruff check scripts/find/ scripts/fix/` clean; every justfile recipe path
    exists on disk; no orphan data files left behind

---

## Phase 3 — add/ + extractor/ directories (31 files)

### 3.1 — add/ directory (5 loose scripts + vagga_codes/ 10 files)

- [x] `scripts/add/add_additions_to_db.py`
  - writes DB · no pyc · refs: none · git: 2024-11-08
  - verdict: archive (user decision, 2026-07-13) — superseded by gui2's "add" and "corrections"
    JSON-based workflow (`gui2/additions_manager.py`, `gui2/corrections_manager.py`). Confirmed:
    its source file `shared_data/additions.tsv` hasn't been touched since May 2025 (340 stale
    rows) and nothing else in the codebase reads/writes it; gui2 pass2 commits new words to the
    DB directly and logs them via the JSON additions/corrections managers instead.
  - archived to `archive/scripts/add/add_additions_to_db.py`; removed `additions_tsv_path` from
    `tools/paths.py` (confirmed unused elsewhere); removed its line from `scripts/add/README.md`;
    no justfile refs; no pyc to clean (none existed). `shared_data/additions.tsv` itself left
    untouched (out of scope — not a file living in `scripts/`, and deleting shared_data is a
    bigger call than this row's procedure covers; flagged to user separately, not deleted)
  - → verify: file in `archive/scripts/add/`; `rg -n "add_additions_to_db|additions_tsv_path"
    tools/paths.py scripts/add/README.md justfile` → 0 matches ✓; `uv run ruff check
    tools/paths.py` clean; `uv run pyright tools/paths.py` → 0 errors, 0 warnings

- [x] `scripts/add/add_words_commentaries.py` (113 lines)
  - no pyc · refs: `scripts/add/README.md:8` (example only) · git: 2025-04-22 (gui2
    missing-cst-words work) · read-only despite name/location — no `db_session.commit()`
    anywhere, just a paginated print loop
  - verdict: keep, freshened (user decision 2026-07-13) — added `pr.tic()`/`pr.toc()`,
    `pr.yellow_title("add words from commentaries")`, `pr.green_title("find most common
    words in commentary without meaning")` at top of `main()`, plus `printer as pr` import.
    Changed batch size from 100 to 50, added q-to-quit option via `pr.green()` prompt.
    Added color legend to module docstring (blue=entry missing meaning, red=not in dict).
    Ruff+format+pyright clean.
  - NOTE: another agent archived this to `archive/scripts/add/` and updated README to
    reference `add_words_ebts.py` instead; user asked to move it back. File restored to
    `scripts/add/`. README reference may need reverting.
  - → verify: ruff check ✓ + format ✓ + pyright ✓ on `scripts/add/add_words_commentaries.py`

- [x] `scripts/add/add_words_ebts.py` (124 lines)
  - read-only (interactive) · no pyc · refs: `scripts/add/README.md:20` · git: 2024-10-28
  - plan said "writes DB" but the code is actually read-only — queries + opens Goldendict,
    never commits; corrected to "read-only (interactive)"
  - verdict: keep + freshen (user decision, 2026-07-13) — recurring manual data-entry tool
  - freshen + user requests: expanded module docstring; `pr.white()` description below the
    yellow_title explaining the workflow; added `main() -> None` + type hints on helper
    functions; added counter that prints "press q to quit" every 5 messages; changed quit key
    from `x` to `q`; removed dead `# TODO` trailing comment; `rich.print` kept for the
    inflection display (deliberate plain print)
  - → verify: `uv run ruff check` + `uv run pyright scripts/add/add_words_ebts.py` → 0 errors, 0 warnings ✓

- [x] `scripts/add/add_words_from_egs_&_commentary_columns.py` (130 lines) → renamed
  `scripts/add/example_word_gap_reviewer.py`
  - no pyc · refs: none · git: none (sweeps only since ≤2025-02) · CORRECTION: read-only despite
    "writes DB" label, no `db_session.commit()` anywhere · flags: `&` in filename made it
    unimportable AND broke shell invocation (user hit `uv run` word-splitting on `&`)
  - verdict: keep + freshen + rename (user decision, 2026-07-13) — renamed to
    `example_word_gap_reviewer.py`; refactored `GlobalData` class-level-session anti-pattern to
    a `@dataclass ReviewState` built lazily in `main()`; module docstring explains the 3 ROUTE
    modes; `pr.yellow_title` added so it announces itself when run; full type hints
  - → verify: `uv run ruff check --fix` + `ruff format` + `pyright` all clean ✓; old filename
    gone; `rg -n "add_words_from_egs"` → 0 matches

- [x] `scripts/add/add_words_random.py`
  - "writes DB" flag was wrong — script is actually read-only (a random word picker/discovery
    tool, never calls `.commit()`); no pyc · refs: none · git: none (sweeps only since 2024)
  - **bug fix (user decision, 2026-07-13):** was checking `meaning_1` for the "needs work"
    signal; user corrected this to `source_1` — the real field that matters for this workflow.
    Renamed `no_meaning` → `no_source` to match.
  - verdict: keep (user decision, 2026-07-13)
  - freshen applied: module docstring rewritten (what + workflow), function docstring, `list[int]`
    on all three lists (was bare `list`), `main() -> None`, added `if word is None: continue`
    guard instead of the `# type: ignore[union-attr]` that was silencing a real (if unlikely)
    `.first()` → `None` case, import order fixed
  - → verify: `uv run ruff check scripts/add/add_words_random.py` clean; `uv run pyright
    scripts/add/add_words_random.py` → 0 errors, 0 warnings

- [ ] ~~`scripts/add/synonym_single.py`~~ — **GHOST: not on disk.** Only
  `scripts/add/__pycache__/synonym_single.cpython-313.pyc` remains (mtime 2026-04-26). No action
  here; pyc removed in Phase 7.

- [x] `scripts/add/vagga_codes/` — 10 files (`__init__.py`, an.py 110, apply.py, dhp_m2.py,
  kn.py 143, kn_suggestions.py 140, mn.py, runner.py, shared.py 217, sn.py) — sutta vagga code
  assignment tools, triaged as a group
  - pyc 2026-04-20 (warm) · git: 2026-04-20 created (#192)
  - investigated with the user: confirmed via `apply.cpython-313.pyc` existing AND spot-checking 3
    sample rows from `temp/vagga_codes_AN.tsv` against the live `dpd.db` (headword 53236
    mettāvagga etc. — exact match) that this #192 pass was already run to completion and
    committed. The `temp/vagga_codes_*.tsv` preview files are leftover artifacts from that
    already-applied run, not outstanding pending work.
  - verdict: archive the package (user decision, 2026-07-13 — overriding agent's initial
    keep/freshen recommendation, once "already applied/completed" was confirmed) — but
    `scripts/suttas/vaggas/compile_vaggas.py` only ever imported 2 regex constants
    (`ANY_CODE_RE`, `DPD_CODE_RE`) from `shared.py`'s 217 lines, not the whole module (confirmed
    via `rg -n "ANY_CODE_RE|DPD_CODE_RE" scripts/suttas/vaggas/compile_vaggas.py`), so those two
    constants were inlined directly into `compile_vaggas.py` rather than moving all of `shared.py`
    (most of which — `load_vagga_runs`, `format_range`, `parse_chapter`, etc. — is
    vagga_codes-specific and would be dead weight in the survivor)
  - archived the whole `scripts/add/vagga_codes/` directory (all 10 files) to
    `archive/scripts/add/vagga_codes/`; inlined `DPD_CODE_RE`/`ANY_CODE_RE` into
    `scripts/suttas/vaggas/compile_vaggas.py`; no justfile/paths.py/README refs existed
  - → verify: `rg -n "vagga_codes" justfile tools/paths.py scripts/add/README.md` → 0 matches;
    `rg -n "scripts\.add\.vagga_codes|scripts/add/vagga_codes"` repo-wide (excluding
    kamma/threads, kamma/archive) → 0 matches; `uv run python -c "import
    scripts.suttas.vaggas.compile_vaggas"` → imports clean; `uv run ruff check
    scripts/suttas/vaggas/compile_vaggas.py` clean; `uv run pyright` → 0 errors, 0 warnings; no
    test files reference either `compile_vaggas` or `vagga_codes` (nothing to break)

### 3.2 — extractor/ directory (16 files; whole package created 2026-02-19 "scripts: extractor")

- [x] `scripts/extractor/extract_cone.py` (186 lines) — extract Cone dictionary via AI
  - justfile `cone` · pyc 2026-02-19 · writes `extract_cone.tsv` (gitignored, paths.py entry)
  - verdict: **keep + freshened** — added module docstring, type hints to `connect_to_openrouter`,
    `process_word`, `main`; added `Path` import
  - → verify: ruff + pyright clean ✓

- [x] `scripts/extractor/extract_cpd.py` (171 lines) — extract CPD dictionary via AI
  - no justfile · no pyc · writes `extract_cpd.tsv` (gitignored, paths.py entry) · same-age
    sibling of extract_cone
  - **real bug found (confirmed by user running it live):** `load_cpd_dictionary()` does
    `json.load()` on `pth.cpd_source_path`, but that path now points to `cpd_clean.db`, an actual
    SQLite database (`entries(id, article_id, headword, webkeyword, html, failed)`). Every other
    consumer (`exporter/mobile/mobile_exporter.py`, the `other-dictionaries` submodule's own
    `cpd.py`) uses `sqlite3.connect` + `SELECT headword, html FROM entries ORDER BY id`. The CPD
    source format was migrated to SQLite and this script never got updated — it crashes
    immediately (`UnicodeDecodeError` trying to JSON-parse a binary sqlite file). User confirmed
    live: same traceback. 570 rows of prior AI-extraction progress exist in the output TSV
    from before the source format changed.
  - checked for overlap with `resources/other-dictionaries/` before the verdict: no duplicate —
    that submodule only scrapes/cleans CPD (`scrapers/cpd/`) and exports it as its own standalone
    dictionary (`dictionaries/cpd/cpd.py`, GoldenDict/MDict formatting only). Neither does AI
    POS/meaning extraction to cross-reference into DPD's own database, which is this script's
    unique job — so it belongs in `scripts/extractor/`, not the submodule.
  - verdict: archive (user decision, 2026-07-13) — not worth fixing right now
  - archived: `extract_cpd.py`, `extract_cpd.tsv` (570-row output, kept for historical record),
    and the two CPD-only helpers `_read_cpd.py` + `_load_cpd.py` (the latter already flagged dead
    — imported by nothing, bonus cleanup) → all moved to `archive/scripts/extractor/`; removed
    `extract_cpd_tsv_path` from `tools/paths.py` (ruff+format+pyright clean on that file after
    the edit); cleaned stale `_read_cpd.cpython-313.pyc`; shared helpers used by the surviving
    `extract_cone.py` (`_ai_extraction`, `_output`, `_pos_mapping`, `_signal_handler`,
    `_word_list`, `_dpd_headwords`, `_tsv_helpers`, `_normalize`) left untouched
  - → verify: `archive/scripts/extractor/` contains all 4 files; `rg -n "extract_cpd"
    tools/paths.py justfile` → 0 matches; `uv run ruff check tools/paths.py` clean

- [ ] `scripts/extractor/` helper modules — triage as a set, driven by the two entry points'
  verdicts and the import graph in Reference maps: `__init__.py`, `_ai_extraction.py` (47),
  `_dpd_headwords.py`, `_load_cone.py`, `_load_cpd.py`, `_normalize.py`, `_output.py`,
  `_pos_mapping.py` (52), `_prompts.py` (35), `_read_cone.py` (39), `_read_cpd.py` (42),
  `_signal_handler.py`, `_tsv_helpers.py`, `_word_list.py`
  - **CPD side already resolved** (this agent, 2026-07-13, alongside `extract_cpd.py`'s archive
    above): `_read_cpd.py` and `_load_cpd.py` (the latter was already flagged dead — imported by
    nothing) both moved to `archive/scripts/extractor/`. `_normalize.py` stays — still used by
    `_read_cone.py`, which the surviving `extract_cone.py` needs.
  - **cone side still open** — remaining verdict depends on `extract_cone.py`'s own row
    (`__init__.py`, `_ai_extraction.py`, `_dpd_headwords.py`, `_load_cone.py`, `_normalize.py`,
    `_output.py`, `_pos_mapping.py`, `_prompts.py`, `_read_cone.py`, `_signal_handler.py`,
    `_tsv_helpers.py`, `_word_list.py` — all currently used only by `extract_cone.py`, which is
    justfile-active and not yet triaged in this plan)
  - verdict: TBD (cone-side helpers, pending `extract_cone.py`'s row)
  - → verify: every surviving helper is imported by a surviving file; no orphan helpers

- [ ] ~~`scripts/extractor/compile_abbreviations_other.py`~~ — **GHOST: deleted by archived
  thread `kamma/archive/20260411_abbreviations_exporter`.** Only a stale pyc remains (mtime
  2026-04-11). No action here; pyc removed in Phase 7.

- [ ] **Phase 3 wrap:** ruff+format+pyright clean on kept add/+extractor/ files; justfile `cone`
  recipe intact; import graph consistent
  - → verify: `uv run ruff check scripts/add/ scripts/extractor/` clean;
    `uv run python -c "import scripts.suttas.vaggas.compile_vaggas"` NOT run (no script
    execution) — instead `rg -n "vagga_codes" scripts/suttas/` confirms import still resolves to
    an existing file

---

## Phase 4 — build/ + bash/ + onboarding/ directories (33 files, pipeline & active)

The active pipeline: justfile + **CI workflows** + contributor onboarding. Nearly everything here
is `freshen`/`improve`; archiving anything CI-referenced is forbidden.

### 4.1 — build/ directory (22 files)

- [x] `scripts/build/api_ca_eva_iti_iva_hi.py`
  - **CI (4 workflows)** · pyc 2026-06-07 · git: 2026-06-07 (#157 refactor) · test exists
  - verdict: keep + freshen (user decision, 2026-07-13) — CI-critical, already well-structured
  - freshen: expanded module docstring to note it writes to DB; fixed typo in display string
    (`apicaeveiti_dict` → `apicaevaitihi_dict`); no behavior change
  - → verify: ruff check ✓ + format ✓ + pyright ✓; `uv run pytest tests/scripts/build/test_api_ca_eva_iti_iva_hi.py` → 3 passed ✓

- [~] `scripts/build/config_github_release.py`
  - **CI (5 workflows — first step of every release build)** · no pyc (CI-only) ·
    git: 2026-06-10 (#157 config consolidation)
  - verdict: TBD (keep — CI-critical)
  - → verify: TBD

- [~] `scripts/build/config_quick_profile.py`
  - justfile `makedict-quick` (run + `reset` arg) · no pyc · git: 2026-06-10
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/build/config_uposatha_day.py`
  - justfile `makedict-all` (`force` arg) · pyc 2026-07-07 · git: 2026-07-07 · imported by
    config_uposatha_reset
  - verdict: TBD (keep — hot)
  - → verify: TBD

- [ ] `scripts/build/config_uposatha_reset.py`
  - justfile `makedict-all`/`makedict-min` (`force` arg) · no pyc · git: 2026-07-07
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/build/cst4_xml_to_txt.py`
  - no justfile/CI · no pyc · git: none substantive since ≤2025-12
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/build/db_rebuild_from_tsv.py` (154 lines)
  - **CI (5 workflows — rebuilds db from backup_tsv in every release build)** · no pyc ·
    git: 2026-04-14 "split headwords tsv into 3 parts, fix header bug"
  - verdict: TBD (keep — CI-critical)
  - → verify: TBD

- [ ] `scripts/build/dealbreakers.py`
  - **CI (3 workflows — release gate)** · no pyc · git: 2026-06-08 (#157 refactor)
  - spec wrongly implied dead (no justfile) — it is a CI release gate
  - verdict: TBD (keep — CI-critical)
  - → verify: TBD

- [ ] `scripts/build/deconstructor_output_add_to_db.py`
  - justfile `decon` + **CI (3 workflows)** · no pyc · git: 2026-07-09 (post-deconstructor-refactor
    cleanup — paths were just verified in that thread) · test exists
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/build/docs_add_indexes.py`
  - **CI (static.yml docs deploy)** · no pyc · git: none substantive since ≤2025-06
  - verdict: TBD (keep — CI)
  - → verify: TBD

- [ ] `scripts/build/docs_update_css.py`
  - **CI (static.yml docs deploy)** · no pyc · git: 2025-04-10 (css single-source-of-truth) ·
    related: `scripts/build/mkdocs_overrides/` html files
  - verdict: TBD (keep — CI)
  - → verify: TBD

- [ ] `scripts/build/ebt_counter.py` (128 lines)
  - **CI (3 workflows)** · pyc 2026-06-08 · git: 2026-06-08 (#157 refactor) · test exists
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/build/families_to_json.py`
  - **CI (3 workflows)** · pyc 2026-07-11 (hottest in scripts/) · git: 2026-06-11 (#157 lazy
    GlobalVars refactor) · test exists
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/build/generate_books_tsv.py` (366 lines)
  - no justfile/CI · no pyc · git: 2026-06-15 (help→reference rename)
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/build/newsletter_scraper.py` (401 lines)
  - justfile `newsletter`/`newsletter-fresh` · pyc 2026-03-12 · git: 2026-05-01 · data:
    `newsletter_processed.json` (tracked, paths.py entry)
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/build/root_has_verb_updater.py`
  - **CI (4 workflows)** · pyc 2026-06-06 · git: 2026-06-06 (#157 refactor + tests) · test exists
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/build/sanskrit_root_families_updater.py` (196 lines)
  - **CI (4 workflows)** · pyc 2026-06-06 · git: 2026-06-06 (#157 refactor + tests) · test exists
  - NOTE: spec claimed a `sanskrit-root-families` justfile recipe — none exists; it's CI-run
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/build/tarball_db.py`
  - **CI (draft_release — packages the db artifact)** · no pyc · git: 2026-07-07 (#157 bz2→xz)
  - verdict: TBD (keep — CI-critical)
  - → verify: TBD

- [ ] `scripts/build/transliterate_bjt.py` (173 lines)
  - no justfile/CI · no pyc · git: none substantive since ≤2025-12
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/build/version_print.py`
  - **CI (draft_release + mobile_release — sets RELEASE_TAG; release-critical)** · no pyc ·
    git: none substantive since 2024 — but DO NOT archive; looks dead by every other signal
  - verdict: TBD (keep — CI-critical)
  - → verify: TBD

- [ ] `scripts/build/zip_goldendict_mdict.py` (134 lines)
  - **CI (draft_release)** · pyc 2026-05-01 · git: 2026-06-09 (#157 guard fix, pathlib, hints)
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/build/zip_wxt_extension.py`
  - no justfile/CI · no pyc · git: 2026-01-25 (#122 wxt version)
  - check whether the wxt exporter (exporter/wxt_extension/) superseded this
  - verdict: TBD
  - → verify: TBD

### 4.2 — bash/ directory (5 files, all justfile; hook-excluded but lint anyway)

- [ ] `scripts/bash/initial_setup_run_once.py`
  - justfile `initial_setup_run_once` + **CI (5 workflows)** · no pyc · git: 2026-02-20
  - verdict: TBD (keep — critical onboarding + CI)
  - → verify: TBD

- [ ] `scripts/bash/initial_build_db.py`
  - justfile `initial_build_db` · pyc 2025-12-12 · git: 2026-02-20
  - **the ONE real hardcoded path: line 13 `touch_file("dpd.db")` → route through
    `ProjectPaths().dpd_db_path`** (read `tools/paths.py` + the callee `touch_file` first to
    verify semantics)
  - verdict: TBD (keep + fix path)
  - → verify: `rg -n '"dpd\.db"' scripts/bash/initial_build_db.py` → 0 matches

- [ ] `scripts/bash/generate_components.py`
  - justfile `generate_components` · pyc 2025-12-31 · git: 2026-07-09 (deconstructor cleanup)
  - the `"dpd.db"` at line 10 is in a COMMENT only — nothing to fix except optionally tidying the
    comment
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/bash/makedict.py`
  - justfile `_logged-makedict` (backing makedict/-quick/-all/-min) · pyc 2025-12-12 ·
    git: 2026-03-12
  - verdict: TBD (keep — primary build entry point)
  - → verify: TBD

- [ ] `scripts/bash/initial_build_db_and_export_all.py`
  - justfile `initial_build_db_and_export_all` · pyc 2025-12-12 · git: 2026-02-20
  - verdict: TBD (keep)
  - → verify: TBD

### 4.3 — onboarding/ directory (6 files — LIVE library code: gui2/main.py imports it; 5 tests exist)

- [ ] `scripts/onboarding/__init__.py`
  - pyc 2026-03-29 · git: 2026-03-03 (#215)
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/onboarding/contributor_setup.py` (295 lines)
  - pyc 2026-07-09 (hot) · git: 2026-07-09 · test exists · imports desktop_shortcut
  - `"dpd.db"` occurrences are NOT simple hardcoded paths: line ~123 matches a GitHub release
    asset NAME (`"dpd.db" in asset["name"]` — must stay a string match); line ~154
    `tar.extract("dpd.db", ...)` extracts a MEMBER NAME from the tarball (must match archive
    content — must stay a string). Only replace if you can prove ProjectPaths gives the identical
    string in the contributor's fresh-clone context. When in doubt, leave and note why.
  - verdict: TBD (keep)
  - → verify: onboarding tests pass: `uv run pytest tests/scripts/onboarding/`

- [ ] `scripts/onboarding/contributor_update.py`
  - pyc 2026-07-07 · git: 2026-07-07 · test exists · imported by gui2/main.py · imports
    contributor_setup
  - same asset-name caveat (line ~68); line ~78 `project_root / "dpd.db"` MAY be routable through
    ProjectPaths — verify what `project_root` is relative to ProjectPaths' base_dir before changing
  - verdict: TBD (keep)
  - → verify: onboarding tests pass

- [ ] `scripts/onboarding/data_submission.py`
  - pyc 2026-03-03 · git: 2026-03-04 (#215) · test exists · imported by gui2/main.py
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/onboarding/desktop_shortcut.py`
  - pyc 2026-06-11 · git: 2026-03-03 (#215) · test exists
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] `scripts/onboarding/launch_gui.py`
  - pyc 2026-03-20 · git: 2026-03-03 (#215) · test exists
  - verdict: TBD (keep)
  - → verify: TBD

- [ ] **Phase 4 wrap:** the one real hardcoded path fixed; ruff+format+pyright clean on all
  kept build/+bash/+onboarding/ files; justfile + CI paths untouched-or-consistent
  - → verify: `rg -n '"dpd\.db"' scripts/` → remaining matches are ONLY the documented
    asset-name/tar-member cases (with a code comment or row note explaining each);
    `uv run ruff check scripts/build/ scripts/bash/ scripts/onboarding/` clean;
    `uv run pytest tests/scripts/` passes; `rg -n --hidden "scripts/" .github/ | awk` — every
    CI-referenced path still exists

---

## Phase 5 — suttas/ directory (67 .py files, data-update pipeline)

Parallel processors for source formats (CST, BJT, SC, DPD, DPR) + vagga extractors. These are
infrequent-but-live (run on data updates; #236 AN work touched all five formats in May 2026).
Archive a subdirectory only if its source format is confirmed retired — the May 2026 activity
suggests none are. Expect mostly freshen. TSVs in these dirs are gitignored output
(`scripts/suttas/*/*.tsv`).

### 5.1 — suttas/bjt/ (17 files)

- [ ] `scripts/suttas/bjt/helpers.py` — shared BJT helpers (triage first; others depend on it)
  - pyc 2025-12-11 · git: 2025-12-11 (#186 global-vars refactor)
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/suttas/bjt/an.py` (365 lines)
  - no pyc · git: 2025-12-13 (#186)
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/suttas/bjt/dn.py` · `mn.py`
  - no pyc · git: 2025-12-11 (#186)
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/suttas/bjt/sn.py` (243 lines)
  - no pyc · git: 2026-04-21 (#192 sn web-codes fix)
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/suttas/bjt/kn1_khp.py` · `kn2_dhp.py` · `kn3_ud.py` (pyc 2025-12-09) · `kn4_iti.py`
  · `kn5_snp.py` (287) · `kn6_vv.py` · `kn7_pv.py` · `kn8_thag.py` (255) · `kn9_thig.py` ·
  `kn14_jat.py` (258) — group row, same treatment
  - no pyc (except kn3) · git: 2025-12-18 (#186 kn refactor)
  - memory note: per-book parsers were copy-pasted from prior books — expect stale dead branches;
    flag them, don't rewrite (structural freshen only)
  - verdict: TBD (group)
  - → verify: TBD

- [ ] `scripts/suttas/bjt/an_nipatas.py` · `an_vaggas.py`
  - an_vaggas pyc 2026-05-03 · git: 2026-05-04 (#236)
  - verdict: TBD
  - → verify: TBD

- [ ] stray data: `scripts/suttas/bjt/an.bak.tsv` — manual backup, gitignored
  - likely: delete
  - verdict: TBD
  - → verify: file resolved

### 5.2 — suttas/cst/ (23 files)

- [ ] `scripts/suttas/cst/modules.py` — shared helpers (triage first)
  - pyc 2025-11-19 · git: none substantive since ≤2025-06
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/suttas/cst/main.py` — entry point (imports modules + kn2)
  - no pyc · git: 2025-11-19 (#56 add dhp)
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/suttas/cst/an.py` · `dn.py` · `mn.py` · `sn.py`
  - pyc 2025-11-19 · git: 2025-02-27 (#56 cst rearrange)
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/suttas/cst/kn1–kn6, kn9, kn10, kn12–kn18` (15 files — NO kn7/kn8/kn11)
  - pyc 2025-11-19 mostly, some 2026-02-28 · git: 2025-02-27 (#56), kn2 2025-11-19
  - verdict: TBD (group)
  - → verify: TBD

- [ ] `scripts/suttas/cst/an_nipatas.py` · `an_vaggas.py`
  - an_vaggas pyc 2026-05-03 · git: 2026-05-04/07 (#236)
  - verdict: TBD
  - → verify: TBD

- [ ] stray data: `scripts/suttas/cst/cst copy.tsv` (space in name — manual copy of cst.tsv,
  gitignored)
  - likely: delete
  - verdict: TBD
  - → verify: file resolved

### 5.3 — suttas/sc/ (8 files — NOT 9; `sc.py` is a ghost)

- [ ] `scripts/suttas/sc/main.py.py` — the real SC entry point (imports blurbs, links, modules,
  suttas) with a broken double extension
  - no pyc · git: 2025-02-27 · flags: rename to `main.py`
  - verdict: TBD (likely freshen + rename; update anything referencing the old name —
    `rg -rn "main.py.py" .` first)
  - → verify: no `main.py.py` on disk; imports still resolve

- [ ] `scripts/suttas/sc/modules.py` (imports natural_sort) · `natural_sort.py`
  - pyc 2025-11-19 / 2025-12-10 · git: sweeps only / 2025-02-28
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/suttas/sc/blurbs.py` · `links.py` · `suttas.py` (268 lines)
  - pyc 2025-11-19 · git: 2025-02-28 / 2025-02-27 / 2025-11-19
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/suttas/sc/an_nipatas.py` · `an_vaggas.py`
  - an_vaggas pyc 2026-05-03 · git: 2026-05-04 (#236)
  - verdict: TBD
  - → verify: TBD

- [ ] ~~`scripts/suttas/sc/sc.py`~~ — **GHOST: not on disk**; only `sc.cpython-311.pyc` remains.
  Pyc removed in Phase 7. (`sc.tsv` still exists as gitignored data — decide its fate with the
  sc/ group.)

### 5.4 — suttas/dpd/ (14 files; `tools/paths.py` has `suttas_dpd_dir` pointing here)

- [ ] All 14: `an.py`, `an_nipatas.py`, `an_vaggas.py` (pyc 2026-05-03), `dn.py`, `kn3-ud.py`,
  `kn4-iti.py`, `kn5-snp.py`, `kn6-vv.py`, `kn7-pv.py`, `kn8-th.py`, `kn9-thi.py`, `kn14-ja.py`,
  `mn.py`, `sn.py` — group row, same treatment
  - git: ALL created/rewritten 2026-05-04 (#236 per-source extractors, all books) — recent
  - flags: hyphenated filenames are unimportable as modules (fine for standalone scripts, note
    only); stray `kn8-thi.tsv` data file has no matching script (check whether `kn9-thi.py`
    writes `kn9-thi.tsv` or the stray)
  - `suttas_dpd_dir` in paths.py must keep pointing at a real dir whatever the verdict
  - verdict: TBD (group)
  - → verify: TBD

### 5.5 — suttas/dpr/ (2 files)

- [ ] `scripts/suttas/dpr/an_nipatas.py` · `an_vaggas.py`
  - no pyc · git: 2026-05-04 (#236) — created recently alongside the other formats
  - verdict: TBD
  - → verify: TBD

### 5.6 — suttas/vaggas/ (3 files)

- [ ] `scripts/suttas/vaggas/__init__.py`
  - pyc 2026-04-21 · git: untracked?? — `git ls-files` does NOT list it (global `__init__.py`
    gitignore rule, .gitignore:20) — note and leave
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/suttas/vaggas/compile_vaggas.py` (306 lines)
  - pyc 2026-06-15 (warm) · git: 2026-04-22 (#192) · imports `scripts.add.vagga_codes.shared` ·
    output `compile_vaggas.tsv` is TRACKED + has paths.py entry
  - verdict: TBD (keep — warm, actively used)
  - → verify: TBD

- [ ] `scripts/suttas/vaggas/extract_vaggas.py` (447 lines, largest in suttas/)
  - no pyc · git: 2026-04-21 (#192) · outputs 4 tracked TSVs (extract_vaggas_{bjt,cst,dpd,sc}.tsv)
  - verdict: TBD
  - → verify: TBD

### 5.7 — suttas/ root level

- [ ] `scripts/suttas/find_sutta_alias_candidates.py`
  - no pyc · git: 2026-04-19 (#233 sutta variant resolver)
  - verdict: TBD
  - → verify: TBD

- [ ] **Phase 5 wrap:** ruff+format+pyright clean on kept suttas/ files; strays (`an.bak.tsv`,
  `cst copy.tsv`, `kn8-thi.tsv`) resolved; `main.py.py` renamed
  - → verify: `uv run ruff check scripts/suttas/` clean; `find scripts/suttas -name "*copy*" -o
    -name "*.bak.*"` → nothing; no `main.py.py`

---

## Phase 6 — verse/ + remaining odds and ends

### 6.1 — verse/ directory — delete (user decision 1)

Reality check (2026-07-13): the spec's 14 verse scripts (display, match, normalize, pada_split,
scan, scan_book, scan_book_pretty, summarize_tsv, syllabify, weight, run_dhp_all,
run_dhp_yamakavagga, tests/test_golden, _data/digraphs, _data/metres) are **gone from disk**.
What remains: `scripts/verse/__init__.py` + `scripts/verse/tests/__init__.py` (both git-ignored
via the global `__init__.py` ignore rule, never committed) and 17 stale `.pyc` files
(mtimes 2026-05-27/28). Nothing in the repo imports `scripts.verse`.

- [ ] Delete `scripts/verse/` entirely: `rm -rf scripts/verse/` (removes the two `__init__.py`
  shells, `_data/`, `tests/`, and all `__pycache__/`). Everything inside is untracked/ignored, so
  no git-side cleanup is needed; nothing in the repo references `scripts.verse` (confirm once
  more with `rg -rn "scripts.verse|scripts/verse" . -g '!kamma'` before deleting).
  - verdict: delete (user decision, 2026-07-13)
  - → verify: `scripts/verse/` no longer exists; the rg check above returns nothing outside
    kamma/ docs

### 6.2 — info/, tutorial/, export/, patch/, project_management/ (10 files)

- [ ] `scripts/info/corpus_size.py` (117 lines)
  - read-only · no pyc · refs: none · git: none (sweeps only since ≤2025-02)
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/info/plus_case.py` (61 lines)
  - read-only · no pyc · refs: none · git: none (sweeps only since 2024)
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/info/suffix_counter.py` (78 lines)
  - read-only · no pyc · refs: none · git: none (sweeps only since 2024)
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/tutorial/db_search_example.py` (66 lines)
  - read-only teaching material (keep `print()` here) · no pyc · git: 2025-03-12
  - verdict: TBD (keep — tutorial)
  - → verify: TBD

- [ ] `scripts/tutorial/quick_start.py` (46 lines)
  - read-only teaching material · no pyc · git: 2025-12-22 (moved to tutorials)
  - verdict: TBD (keep — tutorial)
  - → verify: TBD

- [ ] `scripts/export/db_filter_export.py` (89 lines)
  - no refs · no pyc · git: none (sweeps only since 2024)
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/export/sanskrit_export.py` (85 lines)
  - no refs · no pyc · git: 2025-11-17 "add header to sanskrit tsv"
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/patch/patch_dpd.py` (109 lines) — patch goldendict to use local tbw files
  - no refs · no pyc · git: 2026-03-02 created
  - verdict: TBD
  - → verify: TBD

- [ ] `scripts/project_management/project_health_check.py` (281 lines)
  - no refs · no pyc · git: 2026-07-09 (deconstructor-retirement touch — mechanical) ·
    note: possible overlap with the `/dpd` skill's health check — compare before verdict
  - verdict: TBD
  - → verify: TBD

- [ ] **Phase 6 wrap:** ruff+format+pyright clean on all kept remaining files
  - → verify: `uv run ruff check scripts/info/ scripts/tutorial/ scripts/export/ scripts/patch/
    scripts/project_management/` clean

---

## Phase 7 — Cross-cutting cleanup & wrap-up

- [ ] Remove ghost/stale `__pycache__` entries across scripts/ — known ghosts:
  `scripts/add/__pycache__/synonym_single.cpython-313.pyc` ·
  `scripts/extractor/__pycache__/compile_abbreviations_other.cpython-313.pyc` ·
  `scripts/suttas/sc/__pycache__/sc.cpython-311.pyc` · (verse pycs already gone via the Phase
  6.1 delete) · plus any pyc for files archived during this thread, and orphaned
  cpython-311/312 pycs
  - → verify: this script-style check finds nothing: for every `.pyc`, a matching live `.py`
    exists (`find scripts -name "*.pyc" | sed -E 's|__pycache__/||; s|\.cpython-31[123]\.pyc|.py|'`
    — every result exists on disk)

- [ ] Investigate `scripts/prepare_sources.py` referenced by draft_release.yml:231 and
  mobile_release.yml:234 — the path doesn't exist in this repo. Check the workflow steps'
  `working-directory:`; it probably resolves inside a submodule. REPORT ONLY — do not edit
  workflows in this thread.
  - → verify: finding recorded in this plan with the actual resolution

- [ ] Update `scripts/` READMEs to post-triage reality — READMEs exist in: `scripts/`, `add/`,
  `bash/`, `build/`, `cl/`, `export/`, `find/`, `fix/`, `info/`, `onboarding/`, `suttas/`,
  `tutorial/` (patch/ and project_management/ have none — add one-liners only if files survive)
  - → verify: each README lists only existing files/entry points

- [ ] Update `docs/technical/project_folder_structure.md` if layout changed (new `fixme/`,
  removed dirs like `cone/` or `verse/`)
  - → verify: doc matches `find scripts -maxdepth 1 -type d`

- [ ] justfile + CI path integrity after all moves
  - → verify: every path in `rg -n "scripts/" justfile` exists; every path in
    `rg -n --hidden "scripts/" .github/` exists (except the recorded prepare_sources.py finding)

- [ ] Final sweep: `uv run ruff check scripts/ && uv run pyright scripts/ &&
  uv run pytest tests/scripts/`
  - → verify: ruff all-checks-passed; pyright 0 errors on triaged files; pytest passes

- [ ] Verdict summary — report to user: counts of archived, kept+freshened, improved, fixme,
  deleted; list of every justfile/paths.py/README edit made
  - → verify: summary matches the recorded verdicts in this file
