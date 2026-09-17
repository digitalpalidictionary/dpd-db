# Plan — Flet 0.28.3 → 1.0.0 migration

**Spec:** `spec.md` in this directory. Read BR-1 to BR-17 before starting.
**GitHub issue:** none.
**Branch:** `flet-1-0`, in the main working tree. No worktree — user's call.
**Revision:** 8 — applies two independent reviews: BR-17's fix is much smaller
than revision 7 said (store-only constructors), 28 safe sites → 22, two new
BR-14 traps, and C1/C8/C9/C10 dispositions. Revision 7 added the
structural-improvement rule (AD#7, `artifacts/improvements.md`, the Phase 3–6
gate and the Phase 7 audit).
Revision 6 rewrote the plan after Phase 0, Phase 1 and Phase 2a completed and
Phase 2b partially completed.

---

## Where this stands

| Phase | State |
|---|---|
| 0 — read, fetch, reference REPL | done |
| 1 — branch and environment | done |
| 2a — wiring inventory | done |
| 2b — behaviour catalogue | **done** — 415 of 463 bindings, zero uncatalogued; the other 48 are Phase 6 scope |
| 2c — handler timing | **done** — 213 invocations, 6 files; 4 shortlist items unexercised |
| 3 — upgrade, rewrites, renames | not started |
| 4 — threading | not started |
| 5 — automatic updates audit | not started |
| 6 — other Flet consumers | not started |
| 7 — verification and handover | not started |

**Scope change since revision 4.** Phase 3 was specced as a rename pass. It is
now two rewrites plus a rename pass:

- **BR-17** — 23 `self.page = page` assignments inside control subclasses. No
  view constructs until this is done. Per-view constructor rework, not a
  find-and-replace.
- **BR-14** — the tab container. `Tabs.tabs`, `Tabs.on_click`, `Tab.tab_content`
  and `Tab.content` are all gone; the lazy-build mount point moves from a
  per-`Tab` slot to an index in one `TabBarView.controls` list. 6 sites in
  `gui2/main.py`, one of which (Ctrl+S) fails silently.

---

## Architecture decisions

1. **Branch in the main working tree.** The 2.26 GB database and `config.ini`
   are gitignored and survive a branch switch, so the app is runnable on either
   branch with no provisioning and battle-testing happens against real data.
   Verified in Phase 1.

   Three costs, each handled explicitly: one `.venv` holding one Flet, so every
   branch switch is followed by `uv sync --all-groups`; other kamma threads
   share this tree, so every switch is preceded by `git status --porcelain` and
   no whole-tree command is ever run; the live database is in play, so it gets
   backed up before the first migrated build runs.

   The user authorised the agent to run git for **creating and switching to the
   branch only** — not commits, not pushes.

2. **The installed wheel is the authority, not the migration guide.** The guide
   is wrong about `Dropdown.on_change` (BR-1) and buries `self.page` (BR-17) in
   a `UserControl` section this codebase would otherwise skip. Verify in a REPL
   and follow the wheel.

3. **The wiring scanner is AST-based and resolves three layers of
   indirection.** Regex misses handlers threaded through the `Dpd*` wrappers,
   which is where BR-1 lives. It also captures both binding forms — call
   keyword and assignment — because scanning calls alone missed
   `page.on_keyboard_event = ...`, BR-4's own site.

4. **Handler timing hooks the dispatch boundary, not individual controls.**
   `gui2` is lazy-build, so wrapping bound handlers at startup would only see
   the initial screen. Patch the 0.28 event-dispatch path instead. Throwaway
   instrumentation, never committed.

5. **BR-17 before anything else in Phase 3**, then BR-14, then the mechanical
   renames, then threading. Renames need a launchable app; threading needs a
   working one to observe freezes.

6. **The synchronous database layer is not converted.** Blocking calls are
   offloaded to worker threads at the handler boundary.

7. **Structural improvement is allowed where the migration is already rewriting
   the code** — user's decision, 2026-09-17, replacing the earlier "no
   refactors" constraint. The goal is a structurally better app with identical
   behaviour, not a copy of the old one.

   The boundary, the three questions, and what counts as proof are in `spec.md`
   → *Structural improvement — the rule*. The short form: the unit of permission
   is the edit you already have to make; the proof is the wiring diff plus the
   behaviour catalogue entry; everything taken is logged in
   `artifacts/improvements.md`.

   Candidates already identified, with the BR item that would open each file,
   are listed in that same log. They are candidates, not approvals.

8. **Cosmetic renames are still out of scope.** `ft.dropdown.Option` (45 sites),
   the two `ft.border.BorderSide` calls, and the 22 safe `self.page` assignments
   all stay as they are. Renaming for taste is not structural improvement.

9. **No model splitting.** Large, but follows a published guide corrected by
   direct testing.

---

## Phase 0 — Read, fetch, reference REPL ✅

- [x] Read `spec.md` end to end.
  → verify: state BR-1, why the guide cannot be trusted on it, and which two
    capture methods the user chose and rejected.

  BR-1: `Dropdown.on_change` does not exist in 1.0 —
  `TypeError: Dropdown.__init__() got an unexpected keyword argument
  'on_change'`; the fields are `on_select` / `on_text_change`. The guide was
  written against a release candidate and still claims `on_change` survives.
  Chosen: AST wiring inventory + hand-written behaviour catalogue. Rejected:
  driven-UI tests, because the code changes underneath them.

- [x] Fetch the migration guide into `artifacts/flet_1_0_migration_notes.md`,
  every old→new table verbatim, with a header warning about `Dropdown.on_change`.
  → verify: contains the threading table, the services table, the property-rename
    table, and the tabs section.

  50,281 bytes. `curl`, `<article>` extracted, `pandoc -f html -t gfm
  --wrap=none`, so tables are byte-faithful rather than retyped. Grep confirms
  all four: `Background loop`, `page.set_clipboard`, `Icon.name`, `### Tabs`.

- [x] Fetch the companion breaking-changes page.
  → verify: appended under its own heading; any item affecting this codebase is
    cross-checked in the REPL and added to the spec's BR list.

  `/docs/updates/breaking-changes` is a link index. Followed it to the three
  pages that can touch this codebase, each appended verbatim: *All deprecated
  APIs removed* (1.0.0), *`InputBorder` is now a class hierarchy* (1.0.0),
  *Deprecated spacing and border helpers removed* (0.85.0). The fourth 1.0.0
  entry is iOS code-signing — no iOS build here.

  New BR items from this: **BR-14**, **BR-15**, **BR-16**. BR-17 came later,
  from Phase 2b.

  Swept to zero and recorded in the spec's safe list: `e.target`, `DragTarget`,
  `SafeArea`, `SegmentedButton`, `Icon(name=)`, `Card(color=)`, `Badge.text`,
  `Chip.click_elevation`, `BoxDecoration.shadow`, `canvas.Text.text`,
  `NavigationRail*`, `Pagelet`, `Cupertino*Action`, and non-underscored colour
  constants.

- [x] Recreate the isolated reference environment.
  → verify: prints `1.0.0` (via `flet.__version__`; `flet.version.version` is
    gone — BR-12).

  Prints `1.0.0`. It lives in the **session scratchpad** and will not survive
  into a later session. Recreate with:
  `uv venv --python 3.13 fletref && uv pip install --python fletref/bin/python 'flet==1.0.0'`

---

## Phase 1 — Branch and environment ✅

- [x] Snapshot `git status --porcelain` and confirm the current branch.

  Branch `main`. One entry, this thread's own directory:
  `?? kamma/threads/20260917_flet_1_0_migration/`. No other session's work.

- [x] Create and switch to `flet-1-0`.

  `Switched to a new branch 'flet-1-0'`; `git branch --show-current` →
  `flet-1-0`; status identical to the snapshot.

- [x] Tell the user the shared tree is parked on `flet-1-0`.

  Done in the reply that created the branch. Still owed: the same warning as the
  first line of `artifacts/handover.md` in Phase 7.

- [x] Confirm the environment is still on 0.28.3 and complete.

  `flet 0.28.3`; `ruff 0.15.16`.

- [x] Confirm the untracked runtime files survived the switch.

  Path from `tools/paths.py:15` (`base_dir / "dpd.db"`), not from memory.
  `dpd.db` 2,262,204,416 bytes, `config.ini` 1,950 bytes. Opened the database
  through `ProjectPaths` + `get_db_session`, read row 1: `a 1.1`, pos `letter`.

- [x] Launch the editor on the unmigrated branch and screenshot every tab.

  User ran `just gui` and confirmed: clean startup, all 16 tabs render, a word
  loads, PageUp/PageDown scrolls on Pass2Add, Alt+Left/Right and every Alt jump
  key work, Ctrl+S saves. Nothing pre-existing to log.

  16 screenshots in `artifacts/screenshots_before/`, `00_global.png` …
  `15_ct.png` in tab order. Capture order verified against tabs 0, 7 and 15
  before renaming.

  **Hand-off rule for the rest of this thread.** This task asked the user to
  re-verify six behaviours of an app they use daily; five of the six needed no
  human. Only the screenshots did. For Phase 2c, Phase 3 and Phase 7, ask only
  for what the agent cannot produce itself, and say why it needs a human.

**Branch-switching rule.** Switching between `main` and `flet-1-0` does not
switch the installed Flet. Every switch is: `git status --porcelain` →
`git switch <branch>` → `uv sync --all-groups`.

---

## Phase 2 — Baseline capture (still on 0.28.3)

### 2a. Wiring inventory ✅

- [x] Write `artifacts/capture_wiring.py` — an AST scanner over every in-scope
  `.py` file. Emit file, line, control class, and every `on_*` keyword with its
  callable. Stable sorted, diffable. Exclude `__pycache__/`, `build/`,
  `archive/`, `.venv/`, and all non-`.py` files.
  → verify: `gui2/` yields 454 handler bindings by `rg`. Reconcile any drift and
    explain every difference.

  **96 files, 463 bindings** — `gui2` 415, `db_tests/gui` 34,
  `resources/dpd-updater` 14. `ruff` and `pyright` clean.

  A handler can be bound by assignment as well as by keyword. The first version
  scanned call keywords only and missed `page.on_keyboard_event =
  self.on_keyboard` — BR-4's own site — and every `on_tap` in the filter table.
  Both forms are now captured; assignments are marked `(assigned)`.

  Reconciliation, `gui2/` only — 415 (AST) vs 454 (`rg`):

  | Count | What it is |
  |---:|---|
  | 395 | call keyword — a binding, in the inventory |
  | 20 | attribute assignment — also a binding, in the inventory |
  | 35 | `on_*` parameter in a `def` |
  | 1 | local variable named `on_tab_focus` (`gui2/main.py:314`) |
  | 3 | commented-out code (`gui2/mixins.py:128,140,141`) |
  | **454** | total |

  395 + 20 = the 415 in the inventory. Nothing unexplained.

  Note: `rg -o 'on_[a-z_]+\s*='` returns 516, not 454 — it matches inside longer
  identifiers. `\bon_[a-z_]+\s*=` returns 454 and reproduces the spec's
  per-handler breakdown.

- [x] Make the scanner resolve the `Dpd*` wrapper indirection.
  → verify: the inventory shows the `field_type="dropdown"` field configs as
    dropdown constructions.

  Resolves three layers: the `Dpd*` class hierarchy;
  `FieldConfig(field_type=...)` → the `create_fields` dispatch, **parsed from
  source at scan time** so a new field type cannot silently drop out; and
  `super().__init__` inside a wrapper. The last was missing on the first run and
  hid `dpd_fields_classes.py:62`, the wrapper's own binding. Zero unresolved
  `super()` rows remain.

  **The verify line's premise was wrong.** 8 dropdown field configs exist, but
  only 2 bind `on_change` — `root_key` (`:153`) and `derivative` (`:199`).
  `pos`, `trans` and `compound_type` bind `on_blur` only; `neg`, `verb` and
  `plus_case` bind nothing. Spec BR-1 corrected.

- [x] Save as `artifacts/wiring_baseline.txt`; record totals here.

  463 rows plus a counts header.

  | Handler | Repo-wide | in `gui2` |
  |---|---:|---:|
  | `on_click` | 228 | 193 |
  | `on_submit` | 69 | 69 |
  | `on_change` | 59 | 53 |
  | `on_blur` | 44 | 44 |
  | `on_focus` | 34 | 34 |
  | `on_hover` | 10 | 10 |
  | `on_keyboard_event` | 9 | 6 |
  | `on_complete` | 2 | 0 |
  | `on_result` | 2 | 0 |
  | `on_tap` | 2 | 2 |
  | `on_blur_callback`, `on_delete`, `on_dismiss` | 1 each | 1 each |

### 2b. Behaviour catalogue ✅

- [x] Write `artifacts/behaviour_catalogue.md`, organised by screen. Per
  handler: what the user does, what they see, and any ordering rules between
  focus, change, blur and submit on the same field.
  - [x] field system — 164 bindings
    - [x] `dpd_fields.py` — all 48 fields, every handler read from its body
    - [x] `dpd_fields_examples.py` — 20 bindings
    - [x] `dpd_fields_commentary.py` — 14
    - [x] `dpd_fields_meaning.py` — 7
    - [x] `dpd_fields_notes.py` — 6
    - [x] `dpd_fields_compound_construction.py` — 5
    - [x] `dpd_fields_family_set.py` — 5
  - [x] pass views (pass1 add/auto, pass2 add/auto/pre, pass2x in-commentary)
        — 94 bindings. Confirms where the database is written: five buttons,
        all in Pass1Add and Pass2Add. Note `Delete` in Pass1Add removes from the
        queue JSON, not from the database, despite the label.
  - [x] tab views (global, compound-type, filter, tests, roots, sandhi,
        translations, bold-search) — 106 bindings
  - [x] popups, shell and standalone windows (app shell, shared popup,
        word-finder, AI search, test manager, username, spelling and sandhi
        find-replace, the two `gui2/utilities/` scripts) — 51 bindings
  → verify: write a throwaway script listing inventory entries with no catalogue
    mention; report that count as zero.

  ✅ **Zero uncatalogued.** 415 of 463 bindings across 35 of 45 files; the
    remaining 48 across 10 files are `db_tests/gui/` and
    `resources/dpd-updater/`, catalogued in Phase 6 with their migration.

    The check is kept rather than thrown away, because Phase 7 walks the
    catalogue again and needs the same answer:
    `artifacts/check_catalogue_coverage.py`, exits non-zero while any in-scope
    file is unmentioned. It matches on path suffix, not bare filename — `main.py`
    exists in three of the scanned trees, and a bare-name match let `gui2/main.py`
    satisfy `db_tests/gui/main.py`.

  **Findings from cataloguing:**

  1. **BR-17** — 23 sites, no view constructs.
  2. **BR-13 confirmed** — Pass1Add + `construction` blur.
  3. **Commit semantics** — no field handler writes to the database; five
     buttons do, all in Pass1Add and Pass2Add.
  4. **BR-17 is masked at startup.** `_warmup_in_background` (`gui2/main.py:328`)
     builds all 16 views on a worker thread inside a bare `except Exception`
     that **discards the exception** and keeps only the tab label. So BR-17
     produces no message. Worse, the label lookup it calls (`_tab_label`, `:355`)
     is itself broken by BR-14, and it runs *inside* the except handler, so its
     `AttributeError` is uncaught and kills the warm-up thread at the first
     failure. Net effect: the window opens, the first tab renders, and no
     snackbar ever appears. **"The app starts" is not evidence BR-17 is fixed** —
     the evidence is the "All tabs and tools ready." snackbar plus opening every
     tab.
  5. **`pyperclip` is a third clipboard path** (`tests_tab_controller.py:698`),
     not a Flet API. Unaffected by BR-5, must not be converted. BR-5's count of 2
     is Flet clipboard calls, not places the app copies.
  6. **`PopUpMixin`'s dialog is built once and reused for the life of the app**
     (`gui2/mixins.py:40`) — the strongest BR-13 frozen-control candidate.
  7. **Generated wiring** — Compound Type's grid handlers and Filter's cell
     editors are built by factories, so the inventory records the factory call
     site, not one row per cell. Expect that shape in the Phase 7 diff.
  8. **Testing trap** — the appbar's `Submit Data` and `Update` buttons render
     only for a non-primary, non-server-contributor user (`gui2/main.py:58-61`).

- [x] Record commit semantics per field: does the value reach the database on
  change, on blur, on submit, or only on an explicit save? Read each handler
  body — do not infer from the name.

  **Uniform: never, until an explicit save.** Read from all 48 handler bodies.
  No field-system handler writes to the database; the only one that opens a
  session (`_search_and_fill_sanskrit`) reads. Handlers validate, autofill,
  clean, write to the `_add` shadow column, and move focus. The commit is the
  view's `Add to DB` / `Test` button.

  A per-field trigger table would be 48 identical rows; the catalogue carries
  the categories table instead.

  This bounds the live-database risk for the field system. The residual risk is
  a handler overwriting another *form* field before save — `var_phonetic` blur
  does that to `synonym` and `var_text` by design, so it gets tested
  deliberately. The pass views and tab views are not yet catalogued, so the risk
  is not yet fully bounded.

- [x] **BR-1 decision table.** For each editable dropdown that currently takes
  `on_change`, record whether it should fire on selection only, or also while
  typing. Default `on_select`, which preserves 0.28.
  → verify: **9 rows** — the 2 field-system dropdowns that bind `on_change`
    (`root_key`, `derivative`) plus the 7 direct `ft.Dropdown` sites. Source the
    list from `artifacts/wiring_baseline.txt`, not the spec's prose. Present in
    the catalogue before Phase 3 touches any dropdown.

  ✅ Table is in the catalogue §1.3. **All 9 rows take `on_select` alone**,
  settled 2026-09-17 on the thread's standing rule: preserve current behaviour.

  `root_key` was the one candidate for also taking `on_text_change` (live gloss
  while typing). Not taken — it is a behaviour change, and `root_key_change`
  calls `db.get_root_string()`, which would put a database read on the keystroke
  path against the 50 ms budget. If ever wanted, it belongs in Phase 4 with
  offloading attached, not as a handler swap in Phase 3.

### 2c. Handler timing measurement

- [~] Write `artifacts/instrument_handlers.py` — throwaway instrumentation that
  hooks the **0.28 event-dispatch boundary** (not individual controls, AD#4) and
  appends `timestamp, file, line, control, handler, duration_ms` to a log.
  → verify: launch, open a lazily-built tab, click something in it. Rows appear
    for that lazily-built view. If not, the hook is at the wrong level.

  Written. It patches `Page.run_thread` and the awaited branch of
  `Page.on_event_async`, which between them cover the **three** routes a handler
  takes in 0.28: an awaited coroutine; a sync handler handed to `run_thread`;
  and the page-level `EventHandler.get_handler` closure (`on_keyboard_event`
  among them), which is one level deeper and stores the *wrapper*, not the
  handler. A first cut that timed only `on_event_async` would have recorded
  `EventHandler.get_handler.<locals>.fn` for every page-level event and ~0 ms
  for every sync one, since `run_thread` returns immediately — so the closure is
  unwrapped to the user's own callable before timing.

  Verified headlessly against all four shapes (sync/async × direct/page-level):
  one row each, correct handler name, durations matching the injected sleeps
  (20.1/30.9/20.1/30.5 ms). `ruff` and `pyright` clean.

  Log: `artifacts/handler_timing.csv`, header
  `timestamp,file,line,control,handler,event,ms`. `run_thread` calls the app
  makes itself (gui2 launches three) are tagged `(app)` / `(run_thread)` rather
  than an event.

  ✅ Live half confirmed by the session below: `translations_view.py` and
  `wordfinder_popup.py` both appear in the log, and neither exists at startup —
  so the hook does reach lazily built views.

- [x] Hand the instrumented build to the user for a normal editing session.
  Give the exact command and the log path, both read from the code that writes
  them. This is one of the hand-offs that genuinely needs a human: the point is
  real usage, not synthetic clicks.
  → verify: the log holds at least a few hundred invocations across at least
    three screens.

  **213 invocations across 6 files.** Short of "a few hundred", comfortably past
  "three screens". The session was mostly Pass2Add, plus the translations tab
  and the word finder.

  User's own report of the session: *"nothing there seemed slow or sluggish.
  worked as normal."* That matches the numbers — see the analysis below. It is
  also the 0.28 responsiveness baseline in the user's own terms, which is what
  Phase 4's gate is ultimately measured against.

- [x] Analyse into `artifacts/slow_handlers.md`: every handler exceeding its
  class threshold — keystroke > 50 ms, focus/blur/submit > 150 ms, plain clicks
  > 300 ms — slowest first, each tagged with class, call-site and blocking
  operation. Report **sample count and spread** per handler. List separately
  every handler of any speed doing genuinely long work, since those need a
  responsive window and a moving progress indicator rather than a lower number.
  → verify: the list names the handlers on the spec's reading-based shortlist —
    the four Sanskrit entry points, the three keystroke-path handlers
    (`family_word_change`, `pattern_change`, `root_key_change`), the two TSV
    re-readers, the CST book search, and the subprocess launches. A known-slow
    operation missing from the list means the instrumentation missed a path.

  Written. Five handlers over budget, two keystroke-path tail offenders, and two
  operations already correctly backgrounded (the 15.5 s startup database
  initialisation and the 4.2 s warm-up).

  **This verify line does not fully pass, and the gap is coverage, not the
  hook.** Present: 3 of the 4 Sanskrit entry points, and all three keystroke-path
  handlers. Absent: the two TSV re-readers, the CST book search, and the
  subprocess launches — none of them was triggered, because the session never
  opened the tabs they live on. The instrumentation demonstrably reaches lazily
  built views (see the task above), so these are unexercised, not missed.

  Also note **44 of the 63 measured handler/event pairs have `n=1`**. Phase 4's
  gate already says a handler measured once is not measured, so every conversion
  candidate gets re-measured before it is converted.

  Two options for the four unmeasured items, user's call: a second session on
  the untouched tabs while still on 0.28, or carry them into Phase 4 measured on
  1.0 only, with no before-picture. Not blocking Phase 3 either way.

  **BR-14 bonus confirmation.** The log shows each tab activation firing
  `_on_tab_activated` twice, once as `click` and once as `change`. Phase 3's
  BR-14 task asks for exactly this observation *before* editing the tab
  container, so that 1.0's single fire is understood as preserved behaviour
  rather than a regression. That prerequisite is now met from real usage.

---

## Phase 3 — Upgrade, rewrites, renames

**Improvement gate, applies to every task in Phases 3 to 6.** Before restructuring
anything beyond what a task strictly requires, run the three questions in
`spec.md` → *Structural improvement — the rule*: is the surrounding code being
rewritten for a BR item anyway; can the wiring diff and the catalogue entry prove
behaviour unchanged; could a reviewer separate the improvement from the migration
in the diff. If all three pass, take it and log it in `artifacts/improvements.md`
with the BR item that opened the file. If any fails, log it as
`NOTICED — NOT TOUCHING` and move on.

**Improvement commits are separate from migration commits** — user's decision,
not a preference. Never mix a restructure into the same commit as a rename or an
API fix, and never into the same hunk. If a file needs both, do the migration
edit first and stop at a committable point, then do the improvement. This is
what makes the rollback rule a single revert rather than an unpicking exercise.

The agent does not run git. Sequence the work so the commits fall out cleanly,
and when handing back say which pending changes are migration and which are
improvement.

- [x] **Decide the BR-17 constructor pattern before touching the first of the 23
  files** (candidate C1 in `artifacts/improvements.md`).
  → verify: the pattern is recorded in `artifacts/improvements.md` before any
    BR-17 edit, and the 23 sites follow it.

  ✅ Decided and recorded in `artifacts/improvements.md` C1, after review found
    the constructors are store-only. Delete the line; leave runtime reads alone;
    parameterise the two `_update_history_dropdown` calls. **C1 is no longer a
    structural improvement — it is the BR-17 fix itself**, so it does not go in
    the improvements log's taken-improvements table.

- [ ] **Back up the live dictionary data before anything on this branch runs
  against it.**

  `just backup` runs the repo's own TSV backup of headwords and roots. Prefer it
  over copying a 2.26 GB file — it is the mechanism the project trusts, it is
  small, and it is diffable. It writes into git-tracked files in a tree shared
  with other kamma threads, so snapshot `git status --porcelain` first and tell
  the user which files changed.

  If a full binary copy is wanted as well, **ask the user where to put it**. Not
  in this thread's `artifacts/` (inside the repo), and not in the home directory.
  → verify: the backup ran, its output files exist and are non-empty, and the
    working-tree changes it produced are listed here by name.

- [ ] Bump the pin to `flet[all]==1.0.0`; `uv sync --all-groups`; grep the
  output for `error:` lines.
  → verify: `uv run python -c "import flet; print(flet.__version__)"` prints
    `1.0.0`. Use `__version__`, not `version.version` (BR-12).

- [ ] **BR-17 — the 23 `self.page = page` assignments inside `ft.Column`
  subclasses.** Do this first; no view constructs until it is done.

  **This is smaller than revision 7 said.** All 23 assignments are store-only —
  AST-checked, zero `__init__` bodies read `self.page`. So:
  - delete the assignment line, all 23, and nothing else;
  - **leave every handler-time `self.page` read alone** — the 1.0 property
    resolves once mounted, and handlers only run then. Do not rewrite the ~1,000
    runtime uses, and do not add a `self._page` mirror;
  - **two real pre-mount uses**, both the same method:
    `_update_history_dropdown` (`pass1_add_view.py:432` called from `:227`,
    `pass2_add_view.py:675` called from `:268`) ends with `self.page.update()`.
    Pass the page in as an argument from constructor scope — not `did_mount`,
    which would move *when* the work happens, and `pass2_add_view.py:936` calls
    the same method from a handler where `self.page` is already correct;
  - expect pyright noise: 1.0 types `.page` as optional, so handlers may need
    asserts. Lint work, not design work.
  → verify: `uv run kamma/threads/20260917_flet_1_0_migration/artifacts/check_self_page.py`
    reports **0 breaks** and all **22 safe** sites still present. It exits
    non-zero while any control-subclass assignment remains. Use it, not a grep —
    a textual replace over `self.page =` fixes 23 and breaks 22.

    Then, in the running app: **the "All tabs and tools ready." snackbar must
    appear at startup**, and every tab must open. "The app starts" proves
    nothing here — the warm-up worker swallows the exception and its own error
    reporting is broken by BR-14, so a fully broken build still shows a window
    and a first tab. See spec BR-17.

- [ ] **BR-6** — 7 entry points: `ft.app(target=main)` → `ft.run(main)`.
  → verify: the editor launches far enough to show a window, even if it then
    errors. `rg 'ft\.app\('` over the scope returns zero.

- [ ] **BR-14 — the tab container.** Not a rename. 2 container sites split into
  `Tabs` + `TabBar` + `TabBarView`; `length=` matching the tab count;
  `Tab.tab_content` → `Tab.label` (this codebase uses `tab_content`, not the
  `Tab.text` the guide's table names).

  The work is relocating the lazy-build mount point. Each `Tab` owns a `content`
  slot today and `gui2/main.py:289,408` assigns the built view into it. In 1.0
  `Tab` has no `content`; bodies live in one `TabBarView.controls` list indexed
  in parallel with `TabBar.tabs`.
  - **Before editing:** confirm in the running 0.28 app that a tab click fires
    `_on_tab_activated` **twice** (both `on_click` and `on_change` are bound at
    `:389`, and `_mounted_tabs` absorbs the duplicate). The 1.0 single fire is
    then the preserved behaviour, not a regression.
  - `:386-404` — rebuild the container; drop `on_click` (gone in 1.0); keep
    `on_change` and `selected_index`. Note `Tabs.content` is a **required
    positional argument** — `ft.Tabs(length=2)` raises `TypeError` — so it
    cannot be filled in after construction the way `tabs=` was.
  - `:289`, `:408` — mount into `TabBarView.controls[index]`.
  - `:230-231` — the Ctrl+S save path reads the tab then its `.content` to find
    the view's save method. **Fails silently**: the `hasattr` checks below it
    just miss, so Ctrl+S quietly stops saving. Re-source the view from
    `self._views`, which already holds it.
  - `:243` — `len(self.tabs.tabs)` must read the new list; this bound check is
    what stops Alt+Right walking off the end.
  - `:355-356` — `_tab_label()` reads `.tab_content` then `.value`. `Tab.label`
    holds the control now; re-read the label from there.
  - `gui2/test_app.py:40,44` — same shape, same fix.
  → verify: all 16 tabs present, in the original order, with the original labels
    and the `Alt+<key>` tooltips. **Open every tab and confirm its view actually
    appears** — an incomplete fix does not raise. Assigning `tab.content` on a
    1.0 `Tab` is silently accepted (it writes to the instance dict and never
    reaches the UI), so leaving the old mount idiom in place gives empty tabs
    with no error and `_mounted_tabs` already marking them built. Confirm each
    view builds on first selection and is not rebuilt on the second. Walk the tabs with the
    arrow keys and the Alt jump keys, including past both ends. Trigger a
    message that calls `_tab_label()` and confirm it names the tab rather than
    printing an index. Press **Ctrl+S on a tab that saves** (Tests or Roots) and
    confirm the save happens — that path fails silently, so "no error" is not
    evidence.

- [ ] **BR-7** — 136 button constructions across 24 files: `ft.ElevatedButton`
  → `ft.Button`, every `text=` → `content=`. Check other button classes for
  `text=` at the same time.
  → verify: `rg 'ElevatedButton'` returns zero; every screen's buttons render
    with the correct labels, against the Phase 1 screenshots.

- [ ] **BR-10 / BR-2 / BR-3** — the constants. 23 padding sites (10 files),
  7 breaking border sites (4 files), 11 alignment sites (8 files), 1
  border-radius site. Three traps and one non-trap:
  - `Padding.symmetric` is keyword-only — positional calls break.
  - Alignment constants are **uppercase**: `ft.Alignment.CENTER`,
    `ft.Alignment.TOP_LEFT`. A prefix-only replace crashes.
  - Only `ft.border.all()` moved. The two `ft.border.BorderSide(...)` calls at
    `gui2/filter_component.py:33,34` still work in 1.0 — leave them, and do not
    "fix" the `ft.border` module reference either.
  - Leave the commented-out alignment at `gui2/mixins.py:137` alone.
  → verify: `rg 'ft\.padding\.|ft\.alignment\.|ft\.border\.all|ft\.border_radius\.'`
    returns zero, while `rg 'ft\.border\.BorderSide'` still returns **2**. Every
    screen renders with unchanged spacing and borders against the Phase 1
    screenshots. These fail at render time, not import time — a clean import
    proves nothing, look at each screen.

- [ ] **BR-8** — dialogs, four patterns, do not blanket-replace: 21 `page.open`
  → `show_dialog`; 14 `page.close` → `pop_dialog`; the single `page.snack_bar =`
  at `gui2/translations_view.py:127` (attribute gone; also carries a stale
  `# type: ignore` to remove); and the legacy overlay-append at
  `gui2/pass1_auto_view.py:193-197` plus its cancel path. All four target
  **synchronous** methods — no async conversion here.
  → verify: open and dismiss every one of the **20 alert dialog constructions**
    and 11 snackbars in the catalogue. Each appears and closes. The count is 20,
    not the 22 a raw grep reports — the extra two are a type annotation
    (`gui2/pass2_add_view.py:78`) and a commented-out block
    (`gui2/mixins.py:131`). Do not migrate or count either.

- [ ] **BR-1** — the dropdowns. Apply the Phase 2b decision table: the 9 sites
  binding `on_change` move to `on_select` (default), or `on_select` plus
  `on_text_change` where the table says so. Start with the `DpdDropdown` wrapper
  (`dpd_fields_classes.py:62`) and its fan-out (`dpd_fields.py:326`).
  → verify: for `root_key`, `derivative` and each of the 7 direct sites, select
    a value in the running app and confirm the handler fires exactly once, with
    the right value, **and that what it then does matches that field's catalogue
    entry** — against the captured 0.28 behaviour, not your expectation of it.
    Then type into an editable one and confirm it does **not** fire unless the
    decision table says it should. Constructing any `Dropdown` with `on_change=`
    raises `TypeError`, so a clean launch is partial evidence only — lazy-built
    views do not construct until opened. Open every view.

- [ ] **BR-4** — `gui2/main.py:260`: the keyboard handler becomes `async def`
  and awaits `scroll_to`.
  → verify: press PageUp and PageDown and watch the middle section scroll.
    **This only responds on the Pass2Add tab** (Alt+E, index 7) — it is the one
    tab view exposing `_middle_section`, per the comment at `:254`. Testing it
    anywhere else proves nothing. Numpad 9 / Numpad 3 are the same keys with Num
    Lock off. A silent no-op is the failure mode — "no error in the log" is not
    evidence.

- [ ] **BR-4, second half** — `gui2/pass2_add_view.py:1360-1368,1395-1397` swap
  the page keyboard handler while the eg dialog is open, and `_eg_kb_handler`
  calls the saved handler directly. Once `on_keyboard` is `async def` that call
  returns an un-awaited coroutine and global keyboard handling stops while the
  dialog is open. Make `_eg_kb_handler` `async def` and `await` the saved
  handler.
  → verify: open the eg dialog and, with it open, press the keys the global
    handler owns — Alt+Left/Right to change tab, PageUp/PageDown. They must
    still work. Dismiss the dialog and confirm the global handler is back.

- [ ] **BR-5** — the 2 clipboard handlers at `gui2/pass2_add_view.py:934,1180`
  become `async def` and `await ft.Clipboard().set(...)`.
  → verify: perform the copy action and paste into another application. The
    correct text arrives.

- [ ] **BR-13** — guard the confirmed unattached-`update()` site:
  `construction_blur` (`dpd_fields.py:1571`) calls
  `compound_type_add_field.update()`, and Pass1Add never mounts the `_add`
  fields. `phonetic_focus` (`:929`) has the same shape but is unreachable in
  Pass1Add. Guard on the control being mounted; the update is correct in
  Pass2Add.
  → verify: in **Pass1Add**, type a construction and blur the field. No
    `RuntimeError`. Then do the same in Pass2Add and confirm the compound-type
    suggestion still appears in the `_add` column.

- [ ] **BR-16** — no code change, visual check only. Confirm the four
  border-colour signals still read correctly against the Phase 1 screenshots:
  invalid filter input (`filter_component.py:487-495`), an example over 300
  characters (`dpd_fields_examples.py:583-587`), a failing test row
  (`tests_tab_view.py:567-577`), and the book dropdown's grey border
  (`dpd_fields_examples.py:191-193`).
  → verify: each goes visibly red when it should and returns to its normal
    border when it should. These fail by looking wrong, not by raising.

- [ ] **Residual sweep.** Grep for each remaining renamed property from the
  guide's table — icon name, card colour, checkbox error, chip elevation, switch
  label style, badge label, box decoration shadows, canvas text value, scroll
  key, segmented-button selection type, Cupertino dialog action flags.
  → verify: paste every grep result here, **including the zero results**. A
    claimed exemption with no pasted result does not count.

- [ ] Phase verification: launch and walk the entire behaviour catalogue.
  → verify: every entry behaves as described, or the deviation is recorded here
    with a cause. UI freezes are expected at this point — that is Phase 4.

---

## Phase 4 — Threading model

- [ ] Port the instrumentation to the 1.0 dispatch boundary and re-run against
  the migrated build; compare to `artifacts/slow_handlers.md`.
  → verify: an updated log exists for 1.0.0 and the handlers that were slow
    before are still slow, proving the measurements are comparable.

- [ ] Convert the slow handlers, slowest first. Per handler choose deliberately:
  thread-offload-with-result when the value is needed; fire-and-forget for
  background work; a yielding generator where the handler reports progress
  mid-execution. Record the choice and reason per handler.
  → verify: after each conversion, perform that action and confirm the window
    stays responsive throughout (draggable, another control clickable) and the
    end result matches the catalogue entry.

- [ ] Audit the pre-existing concurrency: the three `page.run_thread` launches
  and the `threading.RLock` in `gui2/main.py`, the FastAPI server start at
  `gui2/main.py:437`, the raw `threading.Thread` detector-rebuild worker and
  sleep debounce in `gui2/database_manager.py:671,675`, the background filter
  application in `gui2/filter_component.py:239`, and the locks in
  `gui2/toolkit.py`, `gui2/pass1_auto_controller.py`,
  `gui2/pass1_file_manager.py`. `page.run_thread` re-establishes page context
  inside the worker; a raw `threading.Thread` does not — **its `update()` calls
  are the risk, not its locks.**
  → verify: exercise each — cold start and confirm background database
    initialisation and warm-up complete; apply a filter and confirm results
    arrive; trigger the detector rebuild and confirm the debounce still works
    and does not double-fire; confirm the FastAPI server is reachable.

- [ ] Audit the non-database blocking: the 4 subprocess launches to external
  applications, the kill-and-restart sequence with its 3-second and 2-second
  sleeps in `gui2/global_tab_view.py`, and the retry sleeps in
  `gui2/pass1_auto_controller.py`.
  → verify: trigger each external-application launch and confirm the UI does not
    freeze and the external application opens.

- [ ] Phase verification: re-run the instrumentation against the spec's
  responsiveness table.
  → verify: two things, and the second is the gate.
    **(a)** Median and sample count per handler by class; no handler exceeds its
    class threshold. A handler measured once is not measured.
    **(b)** **The window never stops responding on any action.** Walk every
    long-running action — AI calls, book processing, external application
    launches, filter application, detector rebuild — and during each one drag
    the window and click another control. Both must work, and the progress
    indicator must visibly move.

---

## Phase 5 — Automatic updates audit

- [ ] Find every remaining place a control is refreshed before it is attached.
  BR-13's confirmed site is fixed in Phase 3; this is the sweep for the rest.
  Start from the lazy-build paths, the deferred construction in `gui2/main.py`,
  and any refresh inside a constructor or init.

  **Hiding a field is not this problem.** `filter_fields` and `add_to_ui` set
  `field_row.visible = False`; the control stays mounted and `update()` on it is
  safe. Only genuinely unmounted controls raise — in the field system that is
  the `_add` shadow fields in Pass1Add. Do not re-audit all 48 fields.
  → verify: launch and exercise every screen **including the lazily built
    ones** — a screen never opened is a screen never tested. No exception
    raised. Record which call sites changed.

- [ ] **BR-13 second case:** `update()` also raises on a frozen control
  (`"Frozen control cannot be updated."`). New in 1.0, not in the guide, not
  caught by either review.
  → verify: no `RuntimeError` mentioning a frozen control during a full walk of
    the catalogue.

- [ ] Find every handler that refreshes mid-execution to show progress; convert
  to yielding generators.
  → verify: perform each such action and watch the screen — the progress
    indicator visibly changes *during* the operation, not only at the end.

- [ ] Review the 372 manual refresh calls. Most are now harmless no-ops; leave
  them. Remove one only where it is provably wrong. **Do not do a cleanup
  sweep** — this is a migration, not a refactor.
  → verify: state here how many refresh calls changed and why each had to. If
    the answer is "none beyond the two categories above", that is correct.

---

## Phase 6 — The other Flet consumers

Not a trivial rename pass — the updater needs a real service rewrite.

- [ ] Migrate the 7 data-integrity GUI helpers (`db_tests/gui/main.py` plus the
  taddhita, su/dur, negative-compound, two antonym and hyphenation tools).
  Entry point at `db_tests/gui/main.py:166`; otherwise the same renames.
  **None of these needs BR-17 work** — their classes are plain, not controls.
  → verify: launch each; it opens, displays data, and its primary action works.

- [ ] **BR-9** — the updater's file pickers. `resources/dpd-updater/ui_setup.py`
  (lines 113, 131-132) and `ui_main.py` (lines 293, 318-319) both build
  `ft.FilePicker(on_result=cb)` and append it to `page.overlay`. In 1.0
  `FilePicker` is a `Service`: it belongs in `page.services`, and its methods
  (`get_directory_path`, `pick_files`, `save_file`, `upload`) are awaitable and
  return the result directly — the callback dance goes away. Both handlers
  become `async def`. Entry point at `main.py:107`.

  Note `resources/dpd-updater/` carries its own nested `.venv`. Check which
  environment the updater actually runs in before assuming the repo's pin
  applies to it.
  → verify: launch the updater, open both directory choosers, pick a directory
    in each, and confirm the chosen path lands where the old callback put it.
    Run its own test file.

- [ ] Migrate the 2 standalone utilities under `gui2/utilities/` and
  `gui2/test_app.py`.
  → verify: each launches.

---

## Phase 7 — Verification and handover

- [ ] Regenerate the wiring inventory and diff against
  `artifacts/wiring_baseline.txt`; save as `artifacts/wiring_diff.md`.
  → verify: every diff line annotated as an intended rename (button class, tab
    label, dropdown handler), a structural improvement named in
    `artifacts/improvements.md`, or a deliberate change with a reason. **Zero
    unexplained differences.** A handler that vanished without explanation is a
    migration bug, not diff noise. Expect the 11 dropdown `on_change` lines to
    appear as `on_select` — confirm all 11 are accounted for.

- [ ] Audit `artifacts/improvements.md` against the actual diff.
  → verify: every improvement in the log is present in the code, and every
    structural change in the code is in the log. A restructure that is not
    logged is a review finding — it is the thing a reviewer cannot tell apart
    from a migration bug. Re-check each logged row's evidence column still
    holds after the full walk.

- [ ] Walk the entire behaviour catalogue in the migrated app, ticking each
  screen off in the catalogue file itself.
  → verify: every entry confirmed, or the deviation recorded with a cause.

- [ ] Confirm each of BR-1 to BR-17 individually in the running app and record
  the evidence here.
  → verify: a 17-row table, each row naming the observation that confirms it.
    "No error on launch" is not an observation for the silent failures (BR-1,
    BR-4, BR-14's Ctrl+S path, BR-16) — those need someone to watch the
    behaviour happen. BR-15 is a zero-site sweep, confirmed by the grep.

- [ ] `uv run pytest tests/gui2/` on the branch, compared against the same
  command on `main` (re-syncing the environment on each switch).
  → verify: same tests pass. Any test already broken before the migration is
    named here explicitly, not quietly ignored.

- [ ] `uv run pytest tests/` compared against `main`.
  → verify: new failures attributed.

- [ ] Lint and type-check every touched file: `uv run ruff check --fix`,
  `uv run ruff format`, `uv run pyright`, in that order. Then `just typecheck`
  repo-wide.
  → verify: all clean. Touching a file makes you responsible for its
    pre-existing errors, and satisfying the repo-wide checker does not mean the
    per-file checker is happy — run both.

- [ ] Delete the throwaway instrumentation and confirm nothing imports it.
  `capture_wiring.py` and `check_self_page.py` **stay** — the first is needed
  for the Phase 7 diff, the second is BR-17's regression guard.
  → verify: `instrument_handlers.py` is gone and `rg` for its name returns zero.

- [ ] Write `artifacts/handover.md`, covering:
  - **first line, before anything else: the shared working tree is parked on
    `flet-1-0`.** Any other kamma thread that commits lands on the migration
    branch, not `main`.
  - how to launch the migrated app, as a copy of the command actually run
  - **the switch-back procedure, as two literal command pairs** — going to
    `flet-1-0` and returning to `main` each require re-syncing the environment
  - where the database backup is
  - what to watch for while battle-testing: any moment the window stops
    responding, and the silent-failure candidates — dropdown handlers firing on
    selection, PageUp/PageDown scrolling on Pass2Add, Ctrl+S saving, and the
    keyboard shortcuts while the eg dialog is open
  - what is known-different and what is deliberately not migrated
  - **a pointer to `artifacts/improvements.md`**, so that if something misbehaves
    during battle-testing the first question — migration or refactor? — has a
    written answer, and the rollback rule can be applied
  → verify: every command in it was run and its output seen; every path in it
    was read from the code that uses it, not written from memory.

- [ ] Report to the user in plain English and stop. Do not merge, do not commit
  without being asked, do not close anything.
  → verify: the branch exists, is unmerged, and the user knows how to run it.
