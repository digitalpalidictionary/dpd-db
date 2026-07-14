# Spec: scripts/ triage & refresh

**Thread:** 20260713_scripts_triage

## Overview

`scripts/` holds 193 Python files (~19,300 lines) across 14 subdirectories — finders, fixers, builders, sutta processors, extractors, onboarding, and more. After the #157 refactoring wave refreshed `tools/`, `db_tests/`, `gui2/`, `deconstructor/`, and `exporter/`, `scripts/` is the largest untouched area. It has clear rot: hardcoded `"dpd.db"` paths, mixed coding patterns, and no systematic triage has ever been done.

A fresh audit (2026-07-13) found:
- **61% of scripts (118 of 193) have NO `.pyc`** — never executed directly on this machine
- **12 unique scripts** are wired into the `justfile` pipeline (active consumers)
- **4 scripts** still use hardcoded `"dpd.db"` paths (missed by the #157 ProjectPaths sweep)
- **~30+ sutta-processing scripts** are warm but run infrequently (on data updates)
- **~100+ scripts** are cold/frozen — one-off analysis tools, data repair scripts, or dead prototypes

The root `archive/` directory already has `archive/scripts/` with ~100 previously-archived scripts — same convention applies.

## Triage pattern (proven in `db_tests_triage`)

This thread follows the same pattern used successfully for `db_tests/`. The approach is:

### Phase structure
Work proceeds in phases, ordered by difficulty — low-hanging fruit first (orphans, tiny files, easy verdicts), problem children later (big files, live pipeline, naming collisions). Each phase covers one subdirectory or a related group of scripts.

### Per-file dossier
Every script gets a dossier row in `plan.md` with:
- **Path** and one-line description of what it does
- **Size** (line count)
- **DB impact**: `read-only` or `writes DB (N commits)` — critical for safety, since many scripts write to the live `dpd.db`
- **References**: justfile recipes, paths.py entries, sibling imports — tells us whether it's active
- **Last run**: newest `__pycache__` `.pyc` mtime (snapshot 2026-07-13, before any re-runs). Caveat: a `.pyc` is written when a module is *imported*, not when run directly (`python file.py`). So a missing `.pyc` is strong evidence but not proof of disuse. Conversely, a `.pyc` can appear from a sibling import. Treated as a signal, not a verdict.
- **Git**: last non-data-update commit date
- **Flags**: hardcoded paths, bare `print()` statements, FIXME markers, import issues, type-hint gaps

### Verdict menu
At each row, the agent examines the evidence and issues a verdict from:
- **keep** — leave as-is, apply standard freshen
- **freshen** — standard freshen only, no behavior change
- **improve** — real logic/UX work scoped at the row (e.g., convert pickle→JSON, add exceptions file, fix a bug)
- **archive** — move to `archive/scripts/`, remove stale references from justfile/paths.py
- **delete** — for truly worthless cruft (rare; archive preserves history)
- **move to `fixme/`** — script has value but needs a redesign, not a freshen. Parked with inline `# FIXME` notes at top of file explaining what's needed. Any `tools/paths.py` entries retargeted to the new location (not deleted) so the file stays internally consistent.
- **Bespoke mixes** — e.g., "archive script A, but first extract helper function B into `tools/`"

Unlike `db_tests_triage`, the agent does NOT ask the user to run each script. Verdicts are driven by objective signals (pycache freshness, justfile references, script purpose). Dead code is dead regardless of whether it still runs.

### Standard freshen (applied to EVERY surviving file)
Every file that gets a `keep`, `freshen`, or `improve` verdict gets:
- Module + function docstrings
- Modern type hints (`dict[str, str]`, `| None`, not `Dict`/`Optional`)
- `uv run ruff check --fix` + `uv run ruff format` + `uv run pyright` clean
- Minor obvious fixes: bare `print()` → `tools.printer` where sensible, dead commented code out, `id` param renamed if shadows builtin
- A `pr.yellow_title(...)` at the top of `main()` if the script doesn't have one (user decision 2026-07-13)
- Hardcoded `"dpd.db"` routed through `ProjectPaths`
- **Touch a file = own its lint** — every edited file must pass the pre-commit gate

### Archive convention
- Move to `archive/scripts/` (existing directory)
- If the script has a `tools/paths.py` entry, remove it (unlike `fixme/`, an archived file isn't expected to run again)
- If the script has a justfile recipe, remove it and update the recipe
- If the script has associated data files (JSON, pickle, TSV), archive them alongside
- Remove stale `__pycache__/` entries after archiving

### fixme/ convention
- New `scripts/fixme/` directory (parallels `db_tests/single/fixme/`)
- Move script + its data files there
- Add inline `# FIXME` block at top of file explaining what needs work
- Retarget (don't delete) `tools/paths.py` entries to the new path

### Pytest
Where a surviving file has importable pure logic, add a smoke test under `tests/scripts/...` mirroring the source path. Decided per row. Not every script warrants a test — interactive DB-loop tools, one-shot analysis, and scripts that exist only as justfile recipe endpoints typically don't.

### Phase wrap
Each phase ends with a wrap verification task: ruff+pyright clean on the whole phase directory, pytest pass, justfile recipes intact for kept files.

## Subdirectory audit

| Directory | Files | Active pipeline? | Likely verdict distribution |
|---|---|---|---|
| `scripts/bash/` | 5 | Yes (all in justfile) | freshen all |
| `scripts/build/` | 22 | 7 in justfile | triage — some active, some dead |
| `scripts/onboarding/` | 6 | Critical (user-facing) | freshen/improve all |
| `scripts/suttas/` | 68 | ~12 warm, rest cold | triage — parallel processors |
| `scripts/find/` | 27 | 3 in justfile | mostly archive (one-shots) |
| `scripts/fix/` | 22 | 1 in justfile | mostly archive (one-shots) |
| `scripts/extractor/` | 16 | 1 in justfile | triage — cone extractor active |
| `scripts/add/` | 15 | None in justfile | archive (vagga_codes may be warm) |
| `scripts/verse/` | 14 | Warm (May 2026) | freshen (active subproject) |
| Other | 6 | Mixed | info/tutorial: freshen; export/patch: triage |

## Key findings from audit

### Active pipeline (from justfile)
`scripts/bash/initial_setup_run_once.py`, `initial_build_db.py`, `generate_components.py`, `makedict.py`, `initial_build_db_and_export_all.py` — plus `scripts/build/config_quick_profile.py`, `config_uposatha_day.py`, `config_uposatha_reset.py`, `deconstructor_output_add_to_db.py`, `newsletter_scraper.py`, `scripts/extractor/extract_cone.py`, `scripts/fix/pass2exceptions.py`, `scripts/find/variants_process.py`, `scripts/find/comm_not_in_decon_finder.py`, `scripts/find/pass2pre_an_counts.py`

### Hardcoded `"dpd.db"` paths (4 files to fix)
`scripts/bash/initial_build_db.py`, `scripts/bash/generate_components.py`, `scripts/onboarding/contributor_setup.py`, `scripts/onboarding/contributor_update.py`

### `.pyc` freshness clusters
- **Hot (Jul–May 2026):** `build/families_to_json`, onboarding scripts, `fix/pass2exceptions`, `suttas/vaggas/*`, `build/ebt_counter`, `build/api_ca_eva_iti_iva_hi`, `build/sanskrit_root_families_updater`, `build/root_has_verb_updater`, all `verse/` scripts
- **Warm (Apr 2026):** `add/vagga_codes/*`, `extractor/compile_abbreviations_other`
- **Cold (Nov 2025–Mar 2026):** `suttas/cst/*`, `suttas/sc/*` submodules, `extractor/extract_cone` subpackage, `find/most_common_missing_word_finder`
- **Frozen (2023–Aug 2024):** Bare root-level scripts (`backup_*.py`, `anki_csvs.py`, `db_rebuild_from_tsv.py`, `db_to_tsv.py`, etc.) — already in `archive/scripts/` from previous cleanup

### No `.pyc` at all (118 files)
- **Finders (24 of 27):** one-off analysis tools, most never run on this machine. 3 in justfile: `variants_process.py`, `comm_not_in_decon_finder.py`, `pass2pre_an_counts.py`
- **Fixers (17 of 22):** data repair scripts, most never run. 1 in justfile: `pass2exceptions.py` (warm, last run Jun 27)
- **Builders (11 of 22):** mixed — some in justfile, some dead (tarball_db, cst4_xml_to_txt, transliterate_bjt)
- **Sutta processors (~40):** bjt/ dpd/ dpr/ subdirectories — parallel processors, likely warm but infrequent
- **Onboarding (6):** no `.pyc` because this is a developer machine — contributors run these on fresh installs. Treated as active.

### Non-Python directories
- `scripts/cl/` — 10 shell scripts (dpd-anki, dpd-build-db, dpd-gui, etc.) + README. Convenience wrappers, not dead.
- `scripts/cone/` — 2 log files only. Appears to be a stale output directory from a previous extractor run.
- `scripts/server/` — 1 shell script (`update-dpd.sh`). Server management.

## Assumptions & uncertainties

- **pycache as freshness signal**: Treated as evidence, not verdict. A missing `.pyc` doesn't prove a script was never used — it just wasn't *imported* on this machine. Cold + no `.pyc` + no justfile = strong archive signal. Warm `.pyc` + no justfile = investigate (may be a recurring manual tool).
- **Onboarding scripts** have no `.pyc` on this developer machine because they're run on fresh contributor installs, not here. Treated as active pipeline regardless.
- **Sutta processors** (68 files, ~4,000 lines): The CST/BJT/SC/DPD subdirectories are parallel processors for different source formats. They're not "dead" — just infrequent (run on data updates). Archive only if the source format is confirmed retired.
- **Deconstructor hook**: `scripts/build/deconstructor_output_add_to_db.py` is in justfile and may need verification after the deconstructor refactoring wave. Freshen + verify.
- **`scripts/cl/` shell scripts**: Not Python, not in scope for this triage. Document their purpose, leave untouched.
- **`scripts/cone/`**: Likely stale output directory. Clean up log files, archive or delete the directory.
- **`scripts/server/`**: Single shell script. Document, leave alone.
- **Uncertain about `scripts/patch/patch_dpd.py`** and `scripts/project_management/project_health_check.py`** — one-of-a-kind scripts with unclear status. Triage when we reach them.
- **`scripts/session.py`** — appears to be a database session helper at scripts/ root. Only `.py` at root level. Triage in Phase 1.

## Working mode (added 2026-07-13, session 2 — corrected twice, this version is final)

This thread runs **one script at a time, across many sessions.** No phase-by-phase autonomous
execution, no batching, no agent-picked verdicts. Loop, per script:

1. **User says "next."**
2. **Agent responds with exactly three things and then stops — takes no action:**
   - The `uv run <path>` command for that script (so the user can run it themselves without
     guessing invocation syntax — the agent never runs the triaged script itself).
   - A short description of what the script does.
   - A recommendation (verdict + any freshen/logic notes worth flagging).
3. **User decides.** The verdict — keep, archive, delete, fixme, rewrite, whatever — and any
   call about the script's utility or purpose is **always the user's decision**, never the
   agent's. The agent's recommendation is input, not a default to act on.
4. **Only once the user gives explicit go-ahead** does the agent act — and only on what was
   agreed.
5. Routine freshening (modern type hints, docstrings, obvious broken-logic fixes, lint/pyright
   clean) is bundled into that go-ahead automatically once a script is being kept in some form —
   the user doesn't need to separately ask for type hints etc. each time. It is NOT a license to
   also decide the verdict or rewrite behavior — that still requires the user's explicit say.
6. Agent shows the diff. User confirms. Agent waits for the next "next."

**Concurrency marker (added 2026-07-13):** the user runs a second agent in parallel against
this same thread/plan, working a different row at the same time. Before starting step 2 for a
row, the agent MUST mark that row's checkbox `[~]` in `plan.md` (the kamma "in progress"
convention) so the other agent can see it's claimed and skip it. Only flip it to `[x]` once the
user has confirmed the row is done. Always re-read `plan.md`/`spec.md` from disk immediately
before editing either file — the other agent may have written to them since the last read.

The agent must not act — not archive, not delete, not edit, not "helpfully" fix a wrapper script
found along the way — on anything the user hasn't explicitly told it to. This corrects two
failures earlier in this thread: session 1's plan framing ("agent decides verdicts") and an
early session-2 lapse where the agent picked verdicts and executed them (archive session.py,
delete scripts/cone/, edit scripts/cl/ files) before the user had seen a single row. All of that
was reverted except `scripts/cone/`'s two untracked log files, which are unrecoverable — see the
Phase 1 row for `scripts/cone/`.

## Constraints

- Agent never runs the triaged scripts — reads code only.
- No git commands unless explicitly asked; user commits at the end. Phase checkpoints are report-only.
- Touch a file = own its lint: `ruff check` + `ruff format` + `pyright` clean before moving on.
- The justfile must keep working — if a script path changes, update the recipe.
- `scripts/build/deconstructor_output_add_to_db.py` is post-deconstructor pipeline — verify it references the right paths after the recent deconstructor refactoring.
- No migrating scripts to `tools/` unless they're true reusable libraries AND the move is the right call per-row.
- No redesign of the sutta processing pipeline or the verse subproject — structural freshening only.

## How we'll know it's done

- Every script has a recorded verdict in `plan.md` and its implementation is complete.
- All 4 hardcoded `"dpd.db"` paths routed through `ProjectPaths`.
- All surviving scripts: docstrings, modern type hints, ruff + pyright clean.
- `archive/scripts/` and `scripts/fixme/` contain only intentionally-placed files with recorded reasons.
- Stale `__pycache__/` entries cleaned up.
- `uv run pytest tests/scripts/` passes (existing + any new smoke tests).
- `justfile` recipes all point to correct paths.
- `docs/technical/project_folder_structure.md` updated if the subdirectory layout changed.

## What's not included

- No rewriting of business logic in scripts — freshening is structural only.
- No redesign of the sutta processing pipeline.
- No changes to the verse/ subproject beyond structural freshening.
- No interactive user-runs-each-script loop — verdicts are agent-driven from objective signals.
- No migrating scripts to `tools/` — keep them in `scripts/` unless a row's verdict explicitly calls for it.
