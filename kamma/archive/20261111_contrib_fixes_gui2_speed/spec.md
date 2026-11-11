# Spec: contributor server fixes, server memory, laptop gui2 speed

**Thread:** 20261111_contrib_fixes_gui2_speed
**Date:** 2026-11-11
**GitHub issue:** [#215](https://github.com/digitalpalidictionary/dpd-db/issues/215). Never comment on, edit or close the issue.
**Type:** bug fixes + performance.

## Overview

A review of the 74 commits of issue #215 (the contributor web server) found one
fault that must be fixed, four safety faults in the server scripts and gui2, and
three places where a contributor's gui2 process holds memory it never uses. A
second look at the laptop editor found two possible speed gains and one thing
worth measuring.

This thread fixes the faults, cuts the server memory, and makes the laptop
changes only where a measurement on the laptop shows a gain.

**The hard rule of this thread:** the owner's laptop editor (gui2 run as the
desktop app, primary user, all tabs) must not get slower, lose a feature, or
behave differently. Every change is one of:

- **server-gated** — the laptop code path is unchanged (`is_headless_server()`
  is false there, or the changed file never runs on the laptop);
- **pure safety** — the laptop does the same thing, but survives a damaged file;
- **measured laptop gain** — built only when the gate number in the plan is met,
  with the same behaviour.

Each item below says which of the three it is.

## Terms

- **gui2** — the editor, a Flet 1.0 Python app in `gui2/`.
- **Laptop / desktop** — the owner runs gui2 as a desktop app. `is_headless_server()`
  (`tools/server_mode.py`) is false. Saves go to `dpd.db`.
- **Contributor server** — one gui2 process per outside contributor, served as a
  web page behind nginx at `/<user>/`. `is_headless_server()` is true. The db is
  read-only (`PRAGMA query_only = ON`, `db/db_helpers.py`). Saves go to per-user
  JSON files in `DPD_GUI2_DATA_DIR`. Visible tabs: Pass1Add and Transl, plus
  optional Bold Search, DB, √, Infl (`gui2/contributor_tabs.py`). Pass1Auto and
  Pass2 tabs are never visible there.
- **Nightly window** — `scripts/server_contrib/maintenance_window.py`, run by cron
  on the server: stop instances, pull, reconcile, push, rebuild, roll back on
  failure, start instances.
- **Daily pull** — `scripts/server_contrib/contrib_pull.py`, run on the laptop by a
  systemd user timer.
- **Session takeover** — `claim_session(page)` in `gui2/main.py`. One process holds
  one live page. A new page (a reload or a second browser tab) retires the old one.
- **Corpus** — the full list of `DpdHeadword` rows cached in
  `DatabaseManager.db` by `load_corpus()` (`gui2/database_manager.py`).
- **Detector** — `RelationshipDetector` (`tools/synonym_variant.py`), which
  suggests synonyms and variants. It is rebuilt in a background thread after
  every db save.

Background reading: `scripts/server_contrib/README.md`, `gui2/README.md`, the
Flet notes in `CLAUDE.md` ("Docs Lookups"), and the memory results in
`kamma/archive/20261102_contrib_mem_measure/artifacts/results.md`,
`kamma/archive/20261102_contrib_mem_savings/artifacts/results.md` and
`kamma/archive/20261102_contrib_mem_wordfinder_lazy/artifacts/results.md`.

## What it should do

### A. Must fix — the preview dialog and a session takeover (server; laptop behaviour unchanged)

Current behaviour (`gui2/preview.py:220-259`): `_in_progress` is one module-level
flag for the whole process. `preview_and_confirm` sets it and returns at once if
it is already set. Only the dialog's Save or Cancel clears it. Callers:
`gui2/pass1_add_controller.py:194` and `gui2/pass2_add_view.py:971`.

`claim_session` (`gui2/main.py:789-804`) retires the old page by clearing its
controls and its keyboard handler. It does not close the old page's dialogs and
does not touch the flag.

Two failures follow on the server:

1. A contributor clicks "Add to DB", the "Preview before save" dialog opens, and
   the contributor reloads the page (or opens the editor in a second tab). The
   flag stays set. On the new page every later "Add to DB" returns silently. It
   stays dead until the process exits.
2. If the old tab is still open, its dialog's Save still runs. It writes through
   the old page's `AdditionsManager`. The new page's manager was loaded without
   that word, so its next save rewrites the file without it. The old tab showed
   "saved".

Wanted:

- A1. The latch belongs to a page, not to the process. A second call from the
  **same** page while its preview is open still does nothing (today's behaviour,
  kept). A call from a **different** page proceeds.
- A2. The Save button of a retired page saves nothing.
- A3. `claim_session` tells the preview module that the old page is retired, and
  closes every open dialog on the old page.

Laptop: one page per process, so nothing changes there. The existing tests in
`tests/gui2/test_preview.py` must pass unchanged, apart from the fixture line
that resets the old flag.

### B. Safety — a damaged daily-log or presets file must not stop gui2 (pure safety, both)

Current behaviour: `DailyLog._load` (`gui2/daily_log.py:20-26`) and
`FilterPresetsManager.load_presets` (`gui2/filter_presets_manager.py:14-19`)
catch only `FileNotFoundError`. Both `_save` / `save_presets` open the real file
with `"w"` (truncate, then write). Both loaders run inside `ToolKit.__init__`
(`gui2/toolkit.py`). A kill in the middle of a write leaves an empty file, and
`json.load` of an empty file raises `JSONDecodeError`. gui2 then fails to start
for that user, every time, until someone repairs the file by hand.

Wanted, for both files:

- B1. A file that is not valid JSON is moved aside as `<name>.corrupt` (the same
  convention as `gui2/additions_manager.py:55-62`), a red line is printed with
  `pr.red`, and the manager starts empty.
- B2. Saves write a `<name>.tmp` file next to the real one, then `replace` it
  (the same three lines as `AdditionsManager._save_dict`,
  `gui2/additions_manager.py:66-70`). The JSON text written must be byte-for-byte
  what is written today (`indent=4, sort_keys=True` for the daily log;
  `ensure_ascii=False, indent=4` for presets).

### C. Safety — the nightly window (server only; never runs on the laptop)

- C1. **Rollback order and guards.** Current behaviour
  (`maintenance_window.py:332-367`): `_restore_rollback` restores the db, then
  git, then the contributor files, with no guard between them. If the db copy or
  the git reset raises (disk full, `TimeoutExpired`), the contributor files are
  never restored, and the outer handler logs "maintenance aborted before the
  pull", which is false. `shutil.copy2` also writes straight onto `dpd.db`, so a
  failed copy leaves a truncated db for the instances to start on.
  Wanted: restore the contributor files **first**; run each of the three steps in
  its own `try`, logging `ERROR` with the step name on failure and going on to
  the next step; copy the db to a temp name beside it and `os.replace` it. The
  three success log lines keep their exact text (`restored db from …`,
  `restored working tree to …`, `restored contributor files`), because tests and
  the status file read them.
- C2. **A failed start is a failed run.** Current behaviour
  (`maintenance_window.py:498`): the result of `_systemctl("start", …)` is thrown
  away. The run reports `skipped` or `rebuilt` and exits 0 while an editor is
  down. A `TimeoutExpired` there also skips the notice removal and the status
  file. Wanted: a non-empty failure list, or a raised `TimeoutExpired`/`OSError`,
  sets the outcome to `Outcome.FAILED` (so `main()` exits 1), and the rest of the
  `finally` block still runs.

### D. Safety — the daily pull's line check (laptop script, not gui2)

Current behaviour (`contrib_pull.py:64`, `152-180`): `CONTROL_CHARACTERS` leaves
out `\r` (0x0d), and `_check_lines` strips only a `\r` at the end of a line. A
line such as `a\tb\rjunk` passes as one valid two-column line. The merge then
writes the bare `\r` into a shared file (`manual_corrections.tsv`, `checked.csv`,
`user_dictionary.txt`). A reader that treats `\r` as a line break sees an extra
malformed line. Whether a current reader breaks on it was **not** proved; the
check gap itself was read and is certain.

Wanted: `_check_lines` rejects any `\r` that is not directly followed by `\n`,
with the reason `carriage return inside a line`. A file with `\r\n` line endings
still passes, as today.

### E. Server memory (server-gated; laptop path unchanged)

- E1. **No decon set on the server.** `initialize_db`
  (`gui2/database_manager.py:184-198`) always calls
  `get_all_decon_no_headwords()`. Its result, `all_decon_no_headwords`, has one
  reader: `gui2/pass2_pre_controller.py:110` (the Pass2Pre tab, never visible to a
  contributor). On the server the cache can never be saved (read-only db), so
  every start runs the live scan (`database_manager.py:383-401`). Wanted: on the
  server, skip the call. The attribute keeps its initial value, an empty set
  (`database_manager.py:155`). Saving: part of the 121.2 MB `initialize_db` row;
  the share of this set is **not measured**.
- E2. **No AI manager on the server.** `Pass1AutoController.__init__` reads
  `toolkit.ai_manager` (`gui2/pass1_auto_controller.py:47`), which builds every AI
  provider client. On the server the start tab is Pass1Add, whose builder calls
  `self._view(2).controller` (`gui2/main.py:225`) and so builds the hidden
  Pass1Auto view, its controller, and the AI manager, before first paint. The
  warm-up builds it again by name at `gui2/main.py:658`. A contributor has no tab
  that sends an AI request. Wanted: on the server, when tab 2 (Pass1Auto) is not
  visible, Pass1Add gets a `Pass1AutoController` with no view, and the AI manager
  is never built. Saving: 34.4 MB measured on the laptop with 7 providers
  (`contrib_mem_measure` results, row `ai_manager`); the server builds 4
  providers, **not measured** there.
- E3. **Free the old app's data on a session takeover.** `claim_session` leaves
  the old `App`, its `ToolKit` and its `DatabaseManager` alive. Evidence: three
  open pages held 2,059.4 MB against 943.3 MB for one (`contrib_mem_savings`
  results, caveats). A plain reload did not grow memory (+6.2, +0.1, +0.0 MB), so
  the cost shows when two tabs are open at once. Wanted: on the server only, a
  takeover empties the old app's big data (corpus, detector, lookup sets, lazy
  managers, built views) before the new app is built, so the new app reuses that
  memory.
- E4. **A memory limit per instance.** `scripts/server_contrib/dpd-gui@.service`
  has no limit. Wanted: `MemoryHigh=1500M` and `MemoryMax=2G`. Basis: warm
  774.1 MB and peak 943.2 MB after these savings' predecessors
  (`contrib_mem_wordfinder_lazy` results); 1,542.8 MB was the highest ever seen,
  before any saving. The limit saves no memory. It stops one instance from
  starving the others; systemd restarts a killed instance (`Restart=always`).

### F. Laptop gui2 speed (built only when the gate is met)

- F1. **Import each tab's code when the tab is built.** `gui2/main.py` imports 5
  view modules at module top (lines 13-20) and 11 more in `App.__init__` (lines
  115-125), all before the window first paints. Views are already built lazily
  (`_view_builders`). Wanted: each import moves into its builder. Gate: the
  import-time saving measured in plan task 6.1 is at least 0.15 s. Below that,
  do not build; record the numbers.
- F2. **Add one new lemma instead of re-reading all of them.**
  `Pass1AddController._save_previewed_word` calls
  `self.db.get_all_lemma_1_and_lemma_clean()` after every committed save
  (`gui2/pass1_add_controller.py:235`). That queries every `lemma_1` and cleans
  each one. Wanted: for a **new** word (`already_in_db` false) add the one lemma
  to `all_lemma_1` and its clean form to `all_lemma_clean`; an edit of an
  existing word keeps the full refresh. Gate: the full refresh measured in plan
  task 6.3 takes at least 0.10 s (median). Below that, do not build.
- F3. **Measure the after-save detector rebuild. No code change.** After every
  db save, `_detector_rebuild_worker` (`gui2/database_manager.py:909-937`) loads
  the whole corpus again on a private session and rebuilds the detector. Earlier
  figures: corpus load 1.9 s warm, detector build 0.7 to 0.9 s
  (`kamma/archive/20260919_gui2_db_load/spec.md`). The worker cannot simply reuse
  `load_corpus()`: that uses the UI's shared session from a second thread, which
  the code comments warn against. A slim private load (only the detector's
  columns, as `_load_contributor_corpus` does) might be faster, but earlier
  figures show a detector built from slim rows holds **more** memory (123.0 MB
  against 15.5 MB, `lever_results.md`). Wanted here: time and peak memory of both
  variants, written to `artifacts/detector_rebuild.md`, with a one-line
  recommendation. The owner decides on a follow-up thread.

## Assumptions & uncertainties

Verified by reading the code on 2026-11-11 (branch `main`, commit `ab74b1c2`):

- every file and line reference in sections A to F;
- `all_decon_no_headwords` has exactly one reader outside `database_manager.py`
  (`rg --hidden all_decon_no_headwords -g '*.py'`);
- `Pass1AddController` calls only `get_auto_processed_dict` and `remove_word` on
  the Pass1Auto controller, and neither touches `self.ui`;
- `toolkit.ai_manager` readers in gui2: `pass1_auto_controller.py:47`,
  `pass1_auto_view.py:179,183`, `pass2_auto_view.py:159,163`,
  `pass2_auto_control.py:39`, `main.py:658`. `ai_search_window.py` builds its own
  and is off on the server;
- the contributor tab list cannot include Pass1Auto or any Pass2 tab
  (`contributor_tabs.py`);
- on the laptop, the only post-save caller of `get_all_lemma_1_and_lemma_clean`
  is `pass1_add_controller.py:235` (the two calls in `pass2_add_view.py` run only
  for a non-primary user).

Not verified, stated as assumptions:

- No speed figure for the laptop is measured in this spec. F1 and F2 are gated
  on measurements for that reason.
- The memory saved by E1 and E3 is not measured. E3's live check is in the
  rollout phase.
- E3 has a race: if the takeover happens while the old app's database load or
  warm-up thread is still running, that thread can refill some data after the
  release. The cost is only memory, and the next takeover or idle sleep clears
  it. This is accepted.
- E4's numbers are a judgement from the figures above. The owner may change them.
- The import-time measurement in F1 is an upper bound on the first-paint gain,
  not the gain itself.
- Importing gui2 view modules in a probe makes no network request. This was the
  case in `kamma/archive/20260918_gui2_startup_latency/`; it was not re-checked.

## Constraints

- The laptop rule at the top of this spec.
- No git commands by the agent. The owner commits at the end.
- Never write to GitHub.
- Never run `git stash`, `git checkout -- <path>`, `git restore`, `git reset --hard`.
- No server address and no home path in any committed file: write `<server-ip>`
  and `<repo root>`.
- Do not start a full build (`makedict`, deconstructor, db rebuild).
- A memory probe stays under 1.5 GB, and the owner is told in one line before it
  runs.
- gui2 is not started as a GUI by the agent, except where the plan says so.
- Type hints on all new code, modern forms. `Path`, not `os.path`. Comments say
  why, never what.

## How we'll know it's done

1. New tests for A, B, C1, C2, D, E1, E2, E3 exist. Each was seen to fail before
   its fix, and the failure output is pasted in `plan.md`.
2. `uv run pytest tests/gui2 tests/tools tests/scripts tests/db` passes, or every
   failure is shown to fail the same way on unchanged code.
3. `ruff check`, `ruff format` and pyright are clean on every touched file, and
   `just typecheck` reports 0 errors.
4. `artifacts/laptop_speed.md` holds the F1 and F2 measurements, the gate result
   for each, and what was built.
5. `artifacts/detector_rebuild.md` holds the F3 measurement.
6. The desktop guard tests pass: with `is_headless_server()` false, the decon set
   is still loaded, the AI manager is still warmed, Pass1Add still shares the
   Pass1Auto view's controller, and a takeover releases nothing.
7. `scripts/server_contrib/README.md` documents the memory limits.
8. After the owner commits and pushes: the rollout checks in plan Phase 8 pass on
   the server.

## What's not included

Found in the review, reported to the owner, not in this thread:

- Every contributor's gui2 runs as root on the server (`User=` in the unit is
  filled from `id -un`). Needs an owner decision and a server migration.
- A contributor missing from the cron line's `--instance` list is not stopped by
  the window, and a rollback can overwrite their newer files.
- The forced-first-password-change gate may be skipped by an oddly formatted
  `Authorization` header (nginx side not verified).
- A build step that times out may leave its child process running.
- No login rate limit in the nginx templates.
- Non-atomic writes in `gui2/variants.py`, `gui2/spelling.py`,
  `tools/spelling.py`, the processed-entries logs
  (`additions_manager._append_to_log`, `corrections_manager._append_to_log`), and
  `merge_appended_lines` in `merge_contrib_files.py`.
- Open items 8, 9, 12 and 19 of
  `kamma/archive/20261030_contrib_x_problem_children/spec.md`.
- A notice when the daily pull skips all day because gui2 is open (item 30).
- Laptop ideas that change behaviour: compact inflection sets, loading the word
  finder on first use, a default row limit in the DB tab.
- "Option E", one process for all contributors.
- Any change to the detector rebuild itself (F3 is a measurement only).
