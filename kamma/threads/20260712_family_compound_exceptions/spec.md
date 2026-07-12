# Spec: family_compound_exceptions (placeholder — to be filled in)

## GitHub issue
(none yet — likely files under #157, the project-cleanup umbrella, but not confirmed)

## Origin

Spun off from the `20260711_db_tests_triage` thread's Phase 3 (`db_tests/gui/`, formerly `db_tests_gui/`) while triaging `add_family_compound_neg.py`, `add_family_compound_su_dur.py`, and `add_family_compound_taddhita.py`. The user asked for real exceptions-tracking work on all three — a JSON exceptions file registered in `tools/paths.py` — which is design/build work, not a triage-scope freshen, so it was deliberately kept out of that thread. See that thread's `plan.md` Phase 3 note (2026-07-12) for the handoff.

## Overview

`db_tests/gui/` has three near-identical Flet editors (copy-paste siblings — same `UiManager`/`DataAndLogic` shape, same layout, same Commit/Pass/Exit button set) that each find headwords missing a `family_compound`/`family_idioms` value under a different detection rule, and let a user confirm/type the value interactively. All three need a way to permanently skip ("except") a headword so it stops being re-flagged on every run — but each currently does this differently, and none can actually **write** a new exception from the running GUI:

- **`add_family_compound_neg.py`** (negative Pāḷi words, e.g. `akusala`): `neg_exceptions = [4, 385, 386, 387, 2017, 3444, 3445, 3446, 3447]` — a hardcoded Python list at module level. No UI affordance to add to it; growing the list means hand-editing the source file.
- **`add_family_compound_taddhita.py`** (taddhita derivatives): `get_exceptions()` reads `tools.tsv_read_write.read_tsv_dot_dict(pth.internal_tests_path)` — i.e. it parses `db_tests/db_tests_columns.tsv` (the **live, gui2-managed** column-rule TSV — explicitly out of scope for any refactor per the parent thread's spec) looking for the row where `test_name == "family_compound empty taddhita"` and JSON-decodes its `exceptions` column. Read-only: no code path ever writes back to this TSV from this script.
- **`add_family_compound_su_dur.py`** (su/dur/sa/nir-prefixed compounds): same TSV-lookup pattern, keyed on `test_name == "family_compound empty su dur nir"`. Also read-only.

None of the three has an "Exception" button in its Flet UI — only Commit/Pass/Exit.

## Key research finding: existing exceptions data already exists and is richer than the code's own copies

Read live from `db_tests_columns.tsv` on 2026-07-12 (via `read_tsv_dot_dict`), all rows whose `test_name` contains "family_compound":

| test_name | ids |
|---|---|
| `family_compound empty neg` | 17 ids: `[4, 385, 386, 387, 2017, 3444, 3445, 3446, 3447, 35349, 35585, 35950, 35951, 35998, 38838, 38845, 38852]` |
| `family_compound empty taddhita` | 32 ids (see script run or re-query for the full list) |
| `family_compound empty su dur nir` | 3 ids: `[63900, 64132, 77841]` |
| `family_compound empty sa` | 3 ids: `[56543, 56544, 88846]` — **separate row, never consulted by any script** |

Implications:
1. **`add_family_compound_neg.py`'s hardcoded 9-id list is stale** — the TSV already has 17 reviewed ids (8 more than the hardcoded list knows about). Any rewrite should seed from the TSV's 17, not the hardcoded 9.
2. **`add_family_compound_su_dur.py` has a live bug, independent of this feature request**: its `should_process()` regex is `re.findall(r"^(su|dur|sa|nir)\b ", i.construction)` — it explicitly processes `sa`-prefixed compounds — but `get_exceptions()` only reads the `"family_compound empty su dur nir"` row, never the separate `"family_compound empty sa"` row. So the 3 ids already reviewed under "sa" will be re-flagged forever. Whatever JSON-exceptions design replaces this should merge both source lists (or the new file should just accumulate going forward and this is a one-time seed concern).

## What it should do (draft — needs user decisions below before planning)

1. Give each of the 3 scripts a dedicated, writable JSON exceptions file registered in `tools/paths.py` (project convention — see `db_tests/single/`'s many `*_exceptions_path`/`*_exceptions_list` entries for the pattern).
2. Seed each new JSON file from the corresponding `db_tests_columns.tsv` row(s) above (a one-time read, not an ongoing dependency — `db_tests_columns.tsv` stays untouched afterward, consistent with the parent thread's constraint that it's gui2-managed live data).
3. Add an "Exception" button to each script's Flet UI (alongside existing Commit/Pass/Exit), wired to append the current headword's id and persist to its JSON file immediately (matching the pattern already established across `db_tests/single/`'s freshened scripts: write-through, no batching).
4. Fix `add_family_compound_su_dur.py` to also honor the `family_compound empty sa` ids (merge at seed time, or keep two lists — TBD, see decisions).

## Open decisions (user to fill in via `/kamma:1-plan`)

1. **JSON shape**: a flat list of ids (matches `neg_exceptions`'s current shape and most of `db_tests/single/`'s `*_exceptions_list.json` files), or a dict keyed by id with a reason/note (more like `test_antonyms.json`'s per-id structure)? Flat list is simpler and matches the majority precedent.
2. **File naming/location**: `db_tests/gui/add_family_compound_neg.json` (co-located, matching most `db_tests/single/` exceptions files) vs. something in `db_tests/gui/storage/` (Flet's own per-session storage dir, currently empty/unused)? Recommend co-located, matching `db_tests/single/` convention.
3. **`su_dur`'s "sa" list**: merge into one combined exceptions file at seed time (simplest), or keep the sa/non-sa distinction as two files matching the TSV's two rows? Recommend merging — the script doesn't distinguish sa from su/dur/nir in its own logic, so one list is enough.
4. **Should the hardcoded hand-authored notes in `add_family_compound_neg.py` (the module-level `neg_exceptions` list) be deleted entirely once the JSON file takes over, or kept as a documented fallback/seed-once constant?** Recommend delete — the JSON becomes the sole source of truth.
5. **Button UI wording/placement**: match the existing Commit/Pass/Exit `ft.TextButton` row, add a 4th "Exception" button — confirm no objection to the visual layout change.
6. **Scope of the taddhita/su_dur rewrite**: do these still need the `read_tsv_dot_dict(pth.internal_tests_path)` read at all after the JSON migration, or is that call fully removable once seeded? Recommend fully removable — keeps these scripts from depending on the live gui2 TSV at all going forward.

## Constraints

- `db_tests/db_tests_columns.tsv` (`pth.internal_tests_path`) is live, gui2-managed data — read from it once to seed, never write to it, and don't leave any of the 3 scripts permanently dependent on it afterward.
- Standard project gates apply: `ruff check --fix` + `ruff format` + `pyright` clean on every touched file; user runs/tests, never the agent (per global rules).
- These 3 files already live at `db_tests/gui/` (moved from `db_tests_gui/` in the parent triage thread, 2026-07-12) — this thread should not need to touch the directory location again, only the files' internals.

## How we'll know it's done

- All 3 scripts have a working, user-confirmed "Exception" button that persists to a dedicated JSON file.
- `add_family_compound_su_dur.py` no longer misses previously-reviewed "sa" ids.
- No script depends on `db_tests_columns.tsv` for exceptions anymore.
- `tools/paths.py` has clean, correctly-named entries for the new files.
- Ruff + pyright clean on all touched files.
