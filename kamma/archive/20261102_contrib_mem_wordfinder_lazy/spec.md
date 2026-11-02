# Spec: no word finder for contributor servers

**Thread:** 20261102_contrib_mem_wordfinder_lazy (the folder name says "lazy"; the owner changed the design to "off", see Decision)
**Date:** 2026-11-02
**GitHub issue:** [#215 — Contributor Onboarding](https://github.com/digitalpalidictionary/dpd-db/issues/215). Never write to the issue.
**Builds on:** `kamma/archive/20261102_contrib_mem_savings/` (its `artifacts/results.md` has the server baseline) and `kamma/threads/20261102_contrib_mem_measure/artifacts/laptop_tables.md` (the cost table).
**Plan:** `plan.md` in this folder.

## Decision (owner, 2026-11-02)

"Contributors do not need the word finder at all." The word finder is for Pass2Add, which nobody has permission to use at the start. So a contributor-server instance never builds it. The first draft of this thread loaded it on the first Ctrl+F; the owner replaced that with "off".

The gate is tied to one thing only: **whether the user has Pass2Add** (tab 7 is among the user's visible tabs). It is not tied to the role. Nobody has Pass2Add at the start, so no contributor builds the word finder; a user who is later given Pass2Add gets it back with no further code.

Consequence the owner accepted by this decision: Ctrl+F also fills in the lemma on Pass1Add (tab 3), which contributors do have (`gui2/main.py:447-451`, `index not in (3, 7)`). Contributors lose Ctrl+F.

## Overview

The word finder (`tools/wordfinder_manager.py`) loads `cst_file_freq.json` (70.9 MB on disk) into Python dicts. It costs **172.1 MB** in isolation and **159.8 MB** in the full build on the laptop (`laptop_tables.md`, 2026-11-02). Every contributor instance builds it at start-up and never uses it. This thread stops that for every instance whose tabs do not include Pass2Add.

Target, not a promise: one instance about 160 MB lower than the 943.3 MB warm and 1,045.7 MB after-one-book figures of the earlier thread (server, commit 247a8429).

## What was verified (read from the source on 2026-11-02)

Sweep: `rg --hidden -n "wordfinder_manager|wordfinder_popup|WordFinderPopup|WordFinderManager"` over the repo, excluding `graphify-out`, `kamma/archive`, `.git`.

- **Users of the word finder:** only `gui2/wordfinder_popup.py:14` (the popup reads `toolkit.wordfinder_manager` when it is built), `gui2/wordfinder_widget.py:16` (no outside reference: dead code, left alone), `gui2/pass1_add_controller.py:51`, and the warm-up (`gui2/main.py:572-573`). Hits in `kamma/threads/20261023_contrib_4_temp_server_test/results.md` are notes.
- **Pass2Add does not call it.** No file named in the sweep belongs to Pass2Add. The word finder is reached only through the popup, which opens on the global Ctrl+F key (`gui2/main.py:308`) on every tab. The popup fills in the lemma on tabs 3 (Pass1Add) and 7 (Pass2Add).
- **Pass1Add builds an unused copy.** `gui2/pass1_add_controller.py:51` stores `toolkit.wordfinder_manager` in `self.wordfinder_manager`. `rg "\.wordfinder_manager" gui2 tests` finds no reader of that attribute. The earlier thread skipped the lazy-managers lever because it assumed Pass1Add used the word finder; that was wrong.
- **Ctrl+W would build it by accident.** `gui2/main.py:311` reads `self.toolkit.wordfinder_popup.is_dialog_open()` on every Ctrl+W, which builds the popup and the word finder on first access.
- **The warm-up builds both.** `_warmup_in_background` touches `toolkit.wordfinder_manager` and `toolkit.wordfinder_popup` for every role (`gui2/main.py:572-573`). The popup's constructor reads the manager, so skipping only the manager line would not help.
- **The shortcut list names both keys.** `gui2/main.py:401` ("Ctrl+F", "Open the word finder ...") and `gui2/main.py:437` ("Ctrl+W", "Close the word finder").
- **The Pass2Add gate exists as data.** `App._visible` (`gui2/main.py:171`, set by `tab_selection()` at `gui2/main.py:48-54`) lists the tab indices the user has. Pass2Add is index 7 (`gui2/main.py:184`). The desktop shows every tab. A contributor gets only `allowed_tabs(...)`: `BASE_TABS`, plus extras that are in `SAFE_TABS` or `READ_TABS` (`gui2/contributor_tabs.py`), so `DPD_GUI2_TABS` cannot add Pass2Add today.
- **Tests exist to copy from:** `tests/gui2/test_main.py::test_server_warmup_builds_only_visible_tabs` and `test_server_shortcut_list_names_only_visible_tabs` (helper `_server_app`), `tests/gui2/test_wordfinder_popup.py`.

## What it should do

When Pass2Add is not among the user's visible tabs (`7 not in self._visible`):

1. The warm-up does not build the word finder or the popup.
2. Ctrl+F does nothing, and Ctrl+W does not ask the popup anything (so nothing builds the popup).
3. The shortcut list does not show the Ctrl+F and Ctrl+W rows.

For every role: `Pass1AddController` stops building its unused copy. The attribute and its import are removed (dead code; the desktop warm-up still builds the manager, so desktop behaviour does not change).

An instance that has Pass2Add, including the desktop (every tab visible), is unchanged. No new setting and no role check: the one condition is `7 in self._visible`.

## Assumptions & uncertainties

Assumed:
- Contributors have only Pass1Auto and Pass1Add by default (`gui2/contributor_tabs.py`). If the owner later grants Pass2Add by changing `contributor_tabs.py`, the word finder builds again by itself, because the one condition is Pass2Add in the visible tabs.
- The laptop saving carries to the server within a few MB, as in the earlier thread.

Not verified (the plan measures each):
- The saving in the full build. The earlier thread showed that per-step numbers can disagree with whole-build numbers, so the plan measures a whole build with and without the word finder.
- That Ctrl+F does nothing visible (no error, no stuck dialog) on the real page.

## Constraints

- No change for any instance that has Pass2Add (the desktop among them). No new dependency. No change to the database file.
- Never read, print or edit `config.ini` or any `.env`. Never touch the live `dpd.db`: probes work on a `.backup` copy. Memory probes follow the standing rules (cap 1.5 GB, watchdog, no stray processes afterwards).
- No git command and no commit by the agent unless the owner asks. The owner pushes; the server agent pulls.
- Server work only through the server agent (host `epitaka`; list the panes first, the title is "OC | dpd contributor"; confirm with `pane read`). Open exactly one page session when measuring: every open page adds a copy of the app to the same process.
- Lint, format and type-check every touched file (`ruff`, `pyright`; for `gui2/` and `tests/` use `--project /dev/null`), run `just typecheck`, and the related tests.

## How we'll know it's done

1. A whole-build probe shows the saving in MB (median, min–max, three runs).
2. Each change has a test written first and a revert check (revert the change, run the test, count the failures).
3. All related tests, `ruff`, `pyright` and `just typecheck` pass. Pre-existing failures are listed, not fixed.
4. The server readings after the change are in `artifacts/server/`, with a before and after table against 943.3 MB (warm) and 1,045.7 MB (one book).
5. On the server page (no Pass2Add), Ctrl+F does nothing and the shortcut list has no Ctrl+F or Ctrl+W row.
6. Parallel reviews (CodeRabbit and pi DeepSeek) are done and every real finding is fixed.

## What's not included

- Loading it on first use, moving the frequency data into the database, or any change inside `tools/wordfinder_manager.py`.
- The "refresh DB" extra memory, the detector rebuild worker, option E (one process for all users).
- `gui2/wordfinder_widget.py` (dead code, not touched).
