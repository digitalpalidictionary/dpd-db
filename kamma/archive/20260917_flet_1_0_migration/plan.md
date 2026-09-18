# Plan — Flet 0.28.3 → 1.0.0 migration

**Spec:** `spec.md` in this directory. Read BR-1 to BR-26 before starting.
**GitHub issue:** none.
**Branch:** `flet-1-0`, in the main working tree. No worktree — user's call.
**Revision:** 14 — the user's Phase 7 test round, 13 of 15 checks passed.
Three new BR items fixed from it: **BR-27** — the big one, `error_text` is dead
on a 1.0 `TextField` while `Dropdown` keeps it, so every validation message in
the editor had silently stopped appearing; **BR-28** dropdown widths; **BR-29**
the `db_tests/gui/` tools freeze because 1.0 runs sync handlers on the event
loop. Two observations logged as follow-ups, not fixed: eg-dialog modality and
the residual focus jumps.
Revision 13 — `resources/dpd-updater` removed from this plan entirely. It
is a dead side project that never belonged in this thread; its submodule is
clean and stays on Flet 0.28.3. BR-9 existed only for it and goes with it, and
Phase 6 is now the `db_tests/gui/` helpers and the standalone utilities only.
Revision 12 — Phase 4 opened. The instrumentation is ported to 1.0's single
dispatch boundary (`BaseControl._trigger_event`, where 0.28 had three routes)
and verified headlessly against all four handler shapes, and the concurrency
audit's reading half is done: the one raw `threading.Thread` turns out to touch
no control, so the task's stated risk is absent, and the real 1.0 question is
cross-thread patch delivery, which only a live start can settle.
Revision 11 — BR-22 done (borders rewritten across 30 files); BR-24 done,
its dead `window.icon` line removed and both desktop entries repointed at the
client's new WM_CLASS, and the window title dropped at the user's request;
BR-23 retested by the user and closed as **not a defect** — the dialog is
modal, and the docstring that said otherwise is wrong; **BR-25** added, found
by measuring the user's screenshot against the 0.28 baseline.
Revision 10 — the user battle-tested the migrated app. Fixed from that:
BR-18 (Ctrl+Q), BR-19 (launch crash), BR-20 (PopupMenuItem), BR-21 (focus/tab
order).
Revision 9 — records Phase 2c and Phase 3 as executed. Three corrections
the reviews did not catch: BR-17 has **four** pre-mount reads, not two (two of
them in `filter_tab_view.py`, found by a new transitive scanner); BR-15 has
**8 sites**, not zero; and a new **BR-18** — `window.close()` is awaitable in
1.0, so Ctrl+Q silently stopped quitting in every Flet app here. Also records
that parts of Phase 6 had to be pulled forward.
Revision 8 — applies two independent reviews: BR-17's fix is much smaller
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
| 3 — upgrade, rewrites, renames | **app runs; every open issue fixed in code, one visual pass left** — BR-22, BR-24 and BR-25 done and awaiting the user's check; BR-23 retested and closed as not a defect. See *Open issues* at the end of Phase 3 |
| 4 — threading | **done** — instrumentation ported, two sessions measured, both audits closed, four conversions landed and confirmed by the user |
| 5 — automatic updates audit | **done** — both pre-mount sweeps clean, frozen case is zero-site, six progress handlers converted |
| 6 — other Flet consumers | **done and user-confirmed** — BR-29 fixed and retested (antonyms sync run end to end) |
| 7 — verification and handover | **done** — wiring diff zero unexplained, improvements audited, suites green, handover written; test round passed 13 of 15, BR-27 to BR-29 fixed and all four retests confirmed. Ready for `/kamma:3-review` |

---

## Phase 7 test round — the user's results

Run 2026-09-18 against `just gui`. **13 of 15 passed.** Numbered as put to them.

| # | Check | Result |
|---|---|---|
| 1 | startup snackbar | ✅ |
| 2 | all 16 tabs open and render | ✅ |
| 3 | dropdown selection does something | ✅ |
| 4 | PageUp/PageDown on Pass2Add | ✅ |
| 5 | shortcuts work with the eg dialog open | ✅ works — **but the user says it shouldn't**; logged as a follow-up, see below |
| 6 | Ctrl+S saves | ✅ |
| 7 | Ctrl+Q quits | ✅ |
| 8 | focus moves to the next field | ⚠️ mostly; a few specific conditions still jump. **User is isolating them and will fix separately** |
| 9 | window never freezes | ✅ |
| 10 | rounded corners | ✅ |
| 11 | field widths | ❌ dropdowns ~65px wider than the text fields → **BR-28** |
| 12 | button labels | ✅ |
| 13 | window title and icon | ✅ |
| 14 | the 7 `db_tests/gui/` helpers | ❌ window freezes on the first click → **BR-29** |
| 15 | the 2 `gui2/utilities/` scripts | ✅ |
| — | Pass2Add **Test** button: failed field's border no longer red | ❌ → **BR-27**, and it was far bigger than the border |

**Retest after the three fixes — all four confirmed by the user, 2026-09-18:**
red borders working; validation messages coming through (the ~60 dead sites of
BR-27); dropdown/text-field right edges aligned (BR-28); and the
`db_tests/gui/` tools working, with antonyms sync run end to end (BR-29).

That closes #11, #14 and the Test-button symptom. Only the two deliberate
follow-ups remain open, both the user's own: eg-dialog modality and the
residual focus jumps.

- [x] **BR-27 — `error_text` is dead on a 1.0 `TextField`.** Full analysis in
  `spec.md`. The reported symptom was one missing red border; the cause was that
  **every validation message in the editor had silently stopped appearing.**
  → verify: the guard flags a dead assignment and passes on the fixed tree; all
    four behaviours (set/clear × TextField/Dropdown) confirmed against the wheel.

  ✅ 1.0 renamed `TextField.error_text` to `error` and **left
  `Dropdown.error_text` alone** — read from dataclass fields, not `dir()`, which
  reports both. `error_text` on a 1.0 `TextField` is not a field at all, so
  assigning it is silently accepted as a dead instance attribute.

  `DpdTextField` subclasses `ft.TextField`, so ~60 sites were writing to
  nothing. `test_manager.py:49` hid it completely: its
  `hasattr(field, "error_text")` guard went False for every text field, so the
  highlighting loop was skipped rather than run-and-failed.

  Two mechanisms, one job each — the rename via an `error_text` property on
  `DpdTextField`/`DpdText` forwarding to `error` (keeping all ~60 call sites
  unchanged), and the red border derived in `before_update()` on both field
  classes, since 1.0 resolves the error state against the theme which BR-22's
  explicit `border=` overrides. Six raw `ft.TextField` sites moved to `error`
  directly.

  **Guard: `artifacts/check_error_text.py`, and its sensitivity is proved.** A
  grep cannot do this — `error_text` is still correct on `Dropdown` and on the
  wrappers — so it walks the AST and flags `.error_text` writes only onto
  attributes built from a bare `ft.TextField(...)`. Reverting one fix made it
  report exactly that site and exit 1; restored in the same command, and the
  restore verified by re-reading the line.

- [x] **BR-28 — dropdown widths.** `DpdDropdown` now takes the same
  `expand=True` as `DpdTextField`, so both resolve identically instead of the
  dropdowns holding a literal 700 while the text fields settled at ~635.
  → verify: both classes report `expand=True`. Right-edge alignment is visual
    and needs the user.

- [x] **BR-29 — the `db_tests/gui/` tools freeze.** All six helpers run a whole
  review session inside the click handler behind `while True: time.sleep(0.1)`.
  0.28 ran sync handlers on a worker thread; 1.0 runs them on the event loop, so
  the window painted once and froze. Fixed in one place — `run_test` in
  `db_tests/gui/main.py` now dispatches via `page.run_thread`, which is where
  0.28 ran it. The six tools are untouched.
  → verify: `check_phase6.py` still exits 0 and the module imports. The freeze
    itself is visual and needs the user.

  Also moved the teardown into a `finally`. It previously ran only on the
  success path, so a raising tool left `running_test` set and every later click
  returned at the guard with no error shown — the tool would just stop
  responding. `NOTICED` while in the file; fixed because the offload made the
  raising path reachable in a way it had not been.

**Two follow-ups, deliberately not done** — both are behaviour changes the user
wants rather than migration regressions, and the thread's rule is to preserve
current behaviour. Recorded in `spec.md` → *Out of scope*:

- **eg dialog modality (#5).** The forwarding is 0.28's behaviour and BR-4's
  second half exists to keep it working. Making the dialog modal means removing
  it — a change in what the app does.
- **residual focus jumps (#8).** BR-21 fixed the general defect; the user is
  isolating the remaining conditions themselves.

**State of the tree after Phase 3.** 43 Python files changed plus
`pyproject.toml` and `uv.lock`.
Green: `uv run pytest tests/` **1886 passed, 12 deselected**; `tests/gui2/`
**284 passed, 0 warnings**; `ruff check` and `ruff format --check` clean on all
43; `uv run pyright` clean on the files it covers; `just typecheck`
**0 errors**.

None of that proves the app runs. Every Phase 3 failure mode that matters is
silent or visual — see the pooled hand-off at the end of Phase 3.

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

  **96 files, 463 bindings** — `gui2` 415, `db_tests/gui` 34, and 14 in a
  directory later removed from scope. **In-scope total: 449.** `ruff` and
  `pyright` clean.

  Phase 7's diff filters the out-of-scope rows out of both sides, so it
  compares 449 against 449.

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

  ✅ **Zero uncatalogued.** 415 of 449 in-scope bindings across 35 files; the
    remaining 34 are `db_tests/gui/`, catalogued in Phase 6 with their
    migration.

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

- [x] **Back up the live dictionary data before anything on this branch runs
  against it.**

  ✅ **Already done by the user, 2026-09-17 07:05**, before the branch was cut —
  so the recipe's self-commit never landed here. Verified rather than taken on
  trust: `db/backup_tsv/dpd_headwords_part_001..003.tsv`, 38.6 / 39.4 / 37.9 MB,
  all timestamped 07:05 today; `dpd_roots_part_001.tsv` 195 KB from 2026-09-15.
  Committed on `main` as `c1064e79 pali update`, which is an ancestor of this
  branch, so the restore point is reachable from here.

  No binary copy taken. The recipe was not run by the agent.

  `just backup` runs the repo's own TSV backup of headwords and roots. Prefer it
  over copying a 2.26 GB file — it is the mechanism the project trusts, it is
  small, and it is diffable. It writes into git-tracked files in a tree shared
  with other kamma threads, so snapshot `git status --porcelain` first and tell
  the user which files changed.

  If a full binary copy is wanted as well, **ask the user where to put it**. Not
  in this thread's `artifacts/` (inside the repo), and not in the home directory.
  → verify: the backup ran, its output files exist and are non-empty, and the
    working-tree changes it produced are listed here by name.

  ⚠️ **DRIFT — `just backup` commits by itself.** Read before running it.
  `backup_dpd_headwords_and_roots` calls `git_commit` unconditionally as its
  last step (`db/backup_tsv/backup_dpd_headwords_and_roots.py:25,148-167`). It
  stages every `dpd_headwords_part_*.tsv` and `dpd_roots_part_*.tsv` and commits
  them as `pali update`, on whatever branch is checked out. This is the
  automated data-update commit habit `CLAUDE.md` warns about, reached from a
  recipe that reads as read-only.

  So `just backup` on this branch would put a `pali update` commit on the
  migration branch, unasked. The agent does not run git in this thread, and this
  recipe runs it on the agent's behalf. **Do not use the recipe as-is.**

  Three ways forward, user's call — recorded 2026-09-17, awaiting a decision:

  a. **Call the two backup functions directly, skipping `git_commit`.** Produces
     the same TSVs, no commit. Leaves the regenerated TSVs as uncommitted
     changes to tracked files in the shared tree — visible to other threads in
     `git status`, but nothing they would sweep, since every thread here stages
     by explicit list. Recommended.
  b. **Binary copy of the 2.26 GB database** to a location outside the repo and
     outside the home directory. Needs a path from the user.
  c. **Skip.** This branch changes no schema and no data-writing code; the risk
     it covers is the migrated editor writing bad data during battle-testing.

  **Not blocking the rest of Phase 3.** The gate is "before anything on this
  branch *runs against* the database". Editing code does not. The pin bump,
  BR-17, BR-14 and the rename passes can all proceed; the backup must land
  before the first launch of a migrated build.

- [x] Bump the pin to `flet[all]==1.0.0`; `uv sync --all-groups`; grep the
  output for `error:` lines.
  → verify: `uv run python -c "import flet; print(flet.__version__)"` prints
    `1.0.0`. Use `__version__`, not `version.version` (BR-12).

  ✅ Prints `1.0.0`. `pyproject.toml:61`. No `error:` lines in the sync output.

  The `[all]` extra resolves differently in 1.0 — worth knowing before anything
  is blamed on the migration itself:

  | | |
  |---|---|
  | dropped | `flet-desktop-light`, `toml` |
  | added | `flet-desktop`, `flet-platform-assets`, `msgpack`, `pillow` |
  | bumped | `flet`, `flet-cli`, `flet-web` → 1.0.0 |

  The desktop runtime changed package: 0.28's `flet-desktop-light` is gone and
  the full `flet-desktop` takes its place. Nothing in the repo names either, so
  no code change follows from it.

  **Note for the rest of the thread:** `gui2/**` is excluded from *both*
  pyright (per `CLAUDE.md`) and pyrefly (`pyproject.toml:105`), the latter
  precisely because flet types `.page` as optional. So BR-17's predicted
  "expect pyright noise — 1.0 types `.page` as optional" largely does not
  materialise for `gui2/`. `ruff` still applies in full.

- [x] **BR-17 — the 23 `self.page = page` assignments inside `ft.Column`
  subclasses.** Do this first; no view constructs until it is done.

  ✅ Done, and **the plan was wrong about the size of it — in the other
  direction this time.** Revision 8 said "delete the assignment line, all 23,
  and nothing else", on the strength of an AST check that no `__init__` body
  reads `self.page`. That check was right and still missed two live bugs,
  because it looked only at `__init__` itself.

  The 23 deletions went in as specified: three distinct spellings
  (`self.page = page`, `self.page: ft.Page = page`,
  `self.page: ft.Page = self.ui.page`), one line each, nothing else touched.
  `check_self_page.py` now reports **0 breaks, 22 safe** and exits 0.

  **Four pre-mount reads, not two.** The plan named
  `_update_history_dropdown` in the two add-views. A transitive scan of
  everything reachable from each constructor found two more, both in
  `gui2/filter_tab_view.py` and both reached the same way:

  | Site | Reached via |
  |---|---|
  | `FilterTabView._add_filter_row` | `__init__` → `_initialize_filters` → here |
  | `FilterTabView._on_column_checkbox_change` | `__init__` → `_initialize_filters` → here |

  Both end in `self.page.update()`, and `_initialize_filters` is called
  unconditionally from `__init__` at three branches. Left alone, opening the
  Filter tab would have raised on construction — and per the plan's own BR-17
  note, the warm-up worker swallows that exception, so it would have surfaced
  as an empty tab with no error rather than as a crash.

  These are also genuine handlers (`on_click=`, `on_change=`), so the page
  could not be added as a leading parameter; it is a trailing optional one
  after the event. A binding is an attribute reference, not a call, so the
  handler path is unaffected.

  All four now take the same shape — the page passed down from constructor
  scope, `(page or self.page).update()` at the use — so no runtime read
  changed and no `did_mount` was introduced.

  **New guard: `artifacts/check_premount_page.py`.** Walks the call graph from
  every control subclass's `__init__` transitively, recognises the
  `(page or self.page)` fix pattern, exits non-zero on anything unguarded.
  Its sensitivity is not assumed: run before the fixes it printed exactly the
  four sites, including the two the plan already knew about; run after, zero.
  It is kept alongside `check_self_page.py` — that one catches the assignment,
  this one catches the consequence.

  Ruff clean on all 23 files. `gui2/**` is excluded from both type checkers
  (see the pin task above), so the predicted assert noise did not appear.

  Still owed, and it needs a human: the **"All tabs and tools ready." snackbar
  at startup**, plus opening all 16 tabs. Blocked until BR-14 and BR-6 land —
  the app cannot start before those.

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
    reports **0 breaks** and the safe sites still present. (The count is **16**
    as of Phase 7, not the 22 this line originally named — 4 were in the
    out-of-scope directory and 2 changed for BR-19.) It exits
    non-zero while any control-subclass assignment remains. Use it, not a grep —
    a textual replace over `self.page =` fixes 23 and breaks 22.

    Then, in the running app: **the "All tabs and tools ready." snackbar must
    appear at startup**, and every tab must open. "The app starts" proves
    nothing here — the warm-up worker swallows the exception and its own error
    reporting is broken by BR-14, so a fully broken build still shows a window
    and a first tab. See spec BR-17.

- [x] **BR-6** — 6 entry points: `ft.app(target=main)` → `ft.run(main)`.
  → verify: the editor launches far enough to show a window, even if it then
    errors. `rg 'ft\.app\('` over the scope returns zero.

  ✅ All 6, exactly as counted: `gui2/main.py`, `gui2/test_app.py`,
  `gui2/ai_search_window.py`, both `gui2/utilities/` scripts,
  `db_tests/gui/main.py`. Every occurrence in scope was dotted (`ft.app`), so
  no local name could collide. The grep now returns zero outside this plan's
  own prose and the fetched guide.

  The throwaway `artifacts/instrument_handlers.py` was updated too, so it still
  launches — though it also imports `flet.core.page`, which 1.0 moved, so it
  needs the Phase 4 port before it runs again.

  Launch verification is owed and needs a human; it is pooled with BR-17's and
  BR-14's below.

- [x] **BR-14 — the tab container.** Not a rename. 2 container sites split into
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

  ✅ Rewritten in both places. The container is now three objects: a `TabBar`
  holding the 16 labels, a `TabBarView` holding the 16 bodies, and a `Tabs`
  wrapping a `Column` of the two. All six named sites done, plus one the plan
  did not list.

  | Site | Change |
  |---|---|
  | build (`main.py`) | `Tabs(tabs=[Tab(tab_content=, content=)])` → `TabBar` + `TabBarView` + `Tabs(content=, length=16)` |
  | eager first tab | `tabs.tabs[0].content =` → `_tab_bodies.controls[0] =` |
  | `_ensure_tab_built` | same, by index |
  | Ctrl+S | re-sourced from `self._views`, not the tab control |
  | Alt+Right bound | `len(self.tabs.tabs)` → `len(self._tab_bar.tabs)` |
  | `_tab_label` | `.tab_content.value` → `.label.value` |
  | `_on_tab_activated` comment | **not in the plan** — it documented the 0.28 double fire as the reason for the dedup guard. Rewritten rather than left to mislead; the guard still earns its place because the keyboard jumps call the handler directly *and* trip `on_change`. |
  | `test_app.py` | same shape, `length=2` |

  `on_click` is dropped as the plan says. Worth recording that the plan's
  reason was slightly off: `on_click` is not gone in 1.0, it moved to
  `TabBar.on_click`. Not binding it is what makes the single fire, and that is
  the deliberate choice.

  **Confirmed against the installed wheel, not the guide** (AD#2), including
  both traps the plan predicted:
  - `Tabs.__init__() missing 1 required positional argument: 'content'` —
    `ft.Tabs(length=2)` really does raise, so the container cannot be filled
    in after construction the way `tabs=` was.
  - assigning `tab.content` on a 1.0 `Tab` is silently accepted and never
    reaches the UI (`hasattr(ft.Tab(label="x"), "content")` is `False`), so
    leaving the old mount idiom would have given 16 empty tabs with no error.
  Also checked: 16 labels build, mount-by-index works, and the label reads back
  through `.label.value`.

  The 0.28 double-fire prerequisite is satisfied from the Phase 2c log rather
  than a special session — every tab activation there appears twice, once as
  `click` and once as `change`.

- [x] **BR-7** — 136 button constructions across 24 files: `ft.ElevatedButton`
  → `ft.Button`, every `text=` → `content=`. Check other button classes for
  `text=` at the same time.
  → verify: `rg 'ElevatedButton'` returns zero; every screen's buttons render
    with the correct labels, against the Phase 1 screenshots.

  ✅ **141 occurrences across 27 files**, not the 136/24 the plan estimated
  (the extra are return annotations such as `-> ft.ElevatedButton`). Grep is
  now zero.

  Two passes, deliberately different in kind. The class rename was a textual
  replace, safe because every occurrence in scope was checked to be dotted
  (`ft.ElevatedButton`, 141 of 141) so no local name could collide. The
  `text=` → `content=` pass was AST-driven, rewriting the keyword only on calls
  to a known 1.0 button class, located by line and column — `text=` is still a
  perfectly good keyword on other controls and a blanket replace would have
  corrupted them. **4 such keywords found.**

  Checked against the wheel first: no 1.0 button class keeps `text=`, and
  `ft.Button`, `FilledButton`, `OutlinedButton`, `TextButton`,
  `FloatingActionButton` and `CupertinoButton` all take `content=`.
  `IconButton` takes neither.

  Screen-by-screen comparison against the Phase 1 screenshots is owed and needs
  a human.

- [x] **BR-10 / BR-2 / BR-3** — the constants. 23 padding sites (10 files),
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

  ✅ **58 replacements across 17 files.** Counts differ from the estimate; the
  actual breakdown, and the greps, are:

  | Old | New | Count |
  |---|---|---:|
  | `ft.padding.all(` | `ft.Padding.all(` | 12 |
  | `ft.padding.only(` | `ft.Padding.only(` | 8 |
  | `ft.padding.symmetric(` | `ft.Padding.symmetric(` | 7 |
  | `ft.alignment.center` | `ft.Alignment.CENTER` | 9 |
  | `ft.alignment.top_left` | `ft.Alignment.TOP_LEFT` | 2 |
  | `ft.border.all(` | `ft.Border.all(` | 7 |
  | `ft.border_radius.all(` | `ft.BorderRadius.all(` | 1 |

  Verify greps, pasted: the four old patterns return **0** in live code and
  **2** in `gui2/mixins.py`, which are the commented-out lines the plan says to
  leave. `ft.border.BorderSide` still returns **2** in
  `gui2/filter_component.py:33,34` (plus 2 in a `gui2/specs/` markdown file,
  not code).

  On the three traps: `Padding.symmetric` is confirmed keyword-only in the
  wheel, and all 7 existing call sites already passed `horizontal=`/`vertical=`,
  so none broke. The uppercase alignment constants are confirmed
  (`Alignment.CENTER` → `Alignment(x=0.0, y=0.0)`). `ft.border.BorderSide`
  still constructs, positionally, and was left alone along with the `ft.border`
  module reference.

  **Sharper than the plan's framing:** the old lowercase modules
  (`ft.padding`, `ft.alignment`, `ft.border_radius`) still *exist* in 1.0 — it
  is only their helper functions that are gone. So these raise
  `AttributeError: module ... has no attribute 'all'` at the moment the line
  executes, which for most of them is view-construction time. The plan is right
  that a clean import proves nothing.

- [x] **BR-8** — dialogs, four patterns, do not blanket-replace: 21 `page.open`
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

  ✅ All four patterns, **21 opens and 14 closes**, exactly as counted. The
  commented-out `page.open` in `gui2/mixins.py` was skipped, as instructed.

  **One semantic difference the plan did not flag, checked in the wheel:
  `pop_dialog()` takes no argument.** 0.28's `page.close(dlg)` named the dialog
  to close; 1.0's `pop_dialog()` closes whichever is topmost. Every call site
  here closes the dialog it just opened with nothing stacked above it, so
  behaviour is preserved — but the argument could not be carried over, and any
  future nested dialog would behave differently.

  The two one-off patterns were done by hand:
  - `gui2/translations_view.py` — `page.snack_bar = ft.SnackBar(..., open=True)`
    became `page.show_dialog(ft.SnackBar(...))`, and the stale `# type: ignore`
    went with it. `SnackBar` is a `DialogControl` in 1.0, so it goes through the
    same call as the alert dialogs.
  - `gui2/pass1_auto_view.py` — the legacy overlay-append
    (`page.overlay.append(dlg)`; `dlg.open = True`) became `show_dialog`, and
    both exits (`handle_text_cancel`, `handle_text_submit`) became
    `pop_dialog()`. Incidentally this drops a latent leak: the old code appended
    the same dialog to `page.overlay` on every button press.

  Opening and dismissing each dialog and snackbar is owed and needs a human.

- [x] **BR-1** — the dropdowns. Apply the Phase 2b decision table: the 9 sites
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

  ✅ All 9, all to `on_select` alone, per the decision table. Confirmed in the
  wheel that `Dropdown.on_change` is gone and `on_select`/`on_text_change`
  exist.

  An AST enumeration found exactly the shape the plan described: **7 direct
  `ft.Dropdown` sites** (`compound_type_tab_view.py` ×2, `dpd_fields_family_set`,
  `filter_tab_view`, `pass1_add_view`, `pass2_add_view`, `roots_tab_view`) plus
  the `DpdDropdown` wrapper, whose single binding fans out to the two
  field-system dropdowns — 9 in total.

  The 7 direct sites were rewritten by AST position. The wrapper keeps its own
  parameter named `on_change` and forwards it to `super().__init__(on_select=)`,
  with a comment saying why. Renaming the wrapper's parameter would mean
  renaming `FieldConfig.on_change` across all 50 field definitions, which is a
  cosmetic rename and out of scope per AD#8. `NOTICED — NOT TOUCHING` for
  anyone who finds the name misleading later.

  Per-dropdown behaviour against the catalogue is owed and needs a human.

- [x] **BR-4** — `gui2/main.py:260`: the keyboard handler becomes `async def`
  and awaits `scroll_to`.
  → verify: press PageUp and PageDown and watch the middle section scroll.
    **This only responds on the Pass2Add tab** (Alt+E, index 7) — it is the one
    tab view exposing `_middle_section`, per the comment at `:254`. Testing it
    anywhere else proves nothing. Numpad 9 / Numpad 3 are the same keys with Num
    Lock off. A silent no-op is the failure mode — "no error in the log" is not
    evidence.

  ✅ `App.on_keyboard` is `async def` and the `scroll_to` call is awaited.
  Confirmed in the wheel that `Column.scroll_to` is a coroutine in 1.0.

- [x] **BR-4, second half** — `gui2/pass2_add_view.py:1360-1368,1395-1397` swap
  the page keyboard handler while the eg dialog is open, and `_eg_kb_handler`
  calls the saved handler directly. Once `on_keyboard` is `async def` that call
  returns an un-awaited coroutine and global keyboard handling stops while the
  dialog is open. Make `_eg_kb_handler` `async def` and `await` the saved
  handler.
  → verify: open the eg dialog and, with it open, press the keys the global
    handler owns — Alt+Left/Right to change tab, PageUp/PageDown. They must
    still work. Dismiss the dialog and confirm the global handler is back.

  ✅ `_eg_kb_handler` is `async def` and awaits the saved handler, with a
  comment recording why. `_restore_eg_kb` and the saved-handler swap are
  unchanged.

- [x] **BR-5** — the 2 clipboard handlers at `gui2/pass2_add_view.py:934,1180`
  become `async def` and `await ft.Clipboard().set(...)`.
  → verify: perform the copy action and paste into another application. The
    correct text arrives.

  ✅ Both, plus the enclosing handlers made `async def`:
  `_click_add_to_db` and `_click_x_button`. Confirmed in the wheel that
  `page.set_clipboard` is gone and `ft.Clipboard().set` is a coroutine.

  Note the catalogue's finding still holds — the `pyperclip` call in
  `tests_tab_controller.py` is a third clipboard path, not a Flet API, and was
  correctly left alone.

  Paste-into-another-application is owed and needs a human.

- [x] **BR-13** — guard the confirmed unattached-`update()` site:
  `construction_blur` (`dpd_fields.py:1571`) calls
  `compound_type_add_field.update()`, and Pass1Add never mounts the `_add`
  fields. `phonetic_focus` (`:929`) has the same shape but is unreachable in
  Pass1Add. Guard on the control being mounted; the update is correct in
  Pass2Add.
  → verify: in **Pass1Add**, type a construction and blur the field. No
    `RuntimeError`. Then do the same in Pass2Add and confirm the compound-type
    suggestion still appears in the `_add` column.

  ✅ Guarded on `compound_type_add_field.page is not None`. The value is still
  assigned either way — only the refresh is conditional — so Pass2Add is
  unaffected and Pass1Add stops raising. `phonetic_focus` left alone, as the
  plan says: same shape, unreachable in Pass1Add.

  Both halves of this need a human to confirm.

- [~] **BR-16** — no code change, visual check only. Confirm the four
  border-colour signals still read correctly against the Phase 1 screenshots:
  invalid filter input (`filter_component.py:487-495`), an example over 300
  characters (`dpd_fields_examples.py:583-587`), a failing test row
  (`tests_tab_view.py:567-577`), and the book dropdown's grey border
  (`dpd_fields_examples.py:191-193`).
  → verify: each goes visibly red when it should and returns to its normal
    border when it should. These fail by looking wrong, not by raising.

  **1 of 4 confirmed, and it took BR-27 to get there.** The user's retest
  confirms the failing-field red border on Pass2Add, which is the same
  `field_border(color=RED)` mechanism as the failing test row — and it was
  genuinely broken until BR-27, so this check earned its place rather than
  rubber-stamping a parity assumption.

  **Still unconfirmed: the other three.** Nobody has typed a 300-character
  example, entered invalid filter input, or looked at the book dropdown's grey
  border. Left `[~]` rather than ticked — the mechanism being shared is an
  argument, not an observation, and this item exists precisely because these
  fail by looking wrong.

- [x] **Residual sweep.** Grep for each remaining renamed property from the
  guide's table — icon name, card colour, checkbox error, chip elevation, switch
  label style, badge label, box decoration shadows, canvas text value, scroll
  key, segmented-button selection type, Cupertino dialog action flags.
  → verify: paste every grep result here, **including the zero results**. A
    claimed exemption with no pasted result does not count.

  ✅ Every result pasted, zeros included. Scope: `gui2/`, `db_tests/`,
  `tests/`, excluding `build/`, `archive/` and markdown.

  | Pattern | Hits |
  |---|---:|
  | `Icon\(name=` | 0 |
  | `Card\([^)]*color=` | 0 |
  | `Checkbox\([^)]*error` | 0 |
  | `click_elevation` | 0 |
  | `Badge\([^)]*text=` | 0 |
  | `BoxDecoration\([^)]*shadow` | 0 |
  | `canvas\.Text\([^)]*text=` | 0 |
  | `scroll_key` | 0 |
  | `SegmentedButton` | 0 |
  | `Cupertino.*Action` | 0 |
  | `is_secondary` | 0 |
  | `ft\.Tab\([^)]*text=` | 0 |
  | `e\.target` | 0 |
  | `DragTarget` | 0 |
  | `SafeArea` | 0 |
  | `Pagelet` | 0 |
  | `version\.version` | 0 |
  | `label_style=` | **71** |
  | `ft\.dropdown\.Option` | **45** |

  Both non-zero results are fine, each checked in the wheel rather than assumed:

  - **`label_style`** survives on `TextField`, `Dropdown`, `Checkbox` and
    `Radio`. Only `Switch` lost it — and none of the 8 `ft.Switch`
    constructions passes `label_style`, so there is nothing to fix.
  - **`ft.dropdown.Option`** still constructs in 1.0, both as `Option("x")` and
    as `Option(key=, text=)`. Left alone per AD#8.

- [x] **BR-15 — `InputBorder`. The plan's premise was wrong: this is not a
  zero-site sweep.** Phase 0 recorded BR-15 as swept to zero, and Phase 7's
  verify line still calls it "a zero-site sweep, confirmed by the grep". There
  are **8 sites** in 5 files.

  They did not break — `ft.InputBorder.OUTLINE` and `.NONE` still resolve in
  1.0 — but each one now emits a `DeprecationWarning` naming removal in 1.3.0,
  and the gui2 test run was printing 9 of them. Found by running the tests, not
  by the grep sweep, because the sweep was looking for the wrong thing.

  Replaced 7 `ft.InputBorder.OUTLINE` → `ft.OutlineInputBorder()` and 1
  `ft.InputBorder.NONE` → `ft.NoInputBorder()`, both names read off the
  deprecation message and confirmed in the wheel. `tests/gui2/` now runs clean:
  **284 passed, 0 warnings** (was 284 passed, 9 warnings).

- [x] **BR-18 (new) — `window.close()` is awaitable in 1.0, and so are
  `destroy`, `center` and `to_front`.** Not in the guide's tables, not in the
  spec's BR list, not caught by either review. Surfaced by `just typecheck`,
  which flagged one instance in `db_tests/gui/` — a file outside gui2, which is
  excluded from both type checkers and would therefore never have reported it.

  A sync call returns an un-awaited coroutine, so **Ctrl+Q silently stops
  quitting**. That is exactly the silent-failure class this thread's spec keeps
  warning about, and it is in every Flet app in the repo.

  7 live sites fixed, each by making the enclosing handler `async def` and
  awaiting the call:

  | File | Handler |
  |---|---|
  | `gui2/main.py` | `App.on_keyboard` (already async for BR-4) |
  | `gui2/global_tab_view.py` | `_click_backup_quit` |
  | `gui2/ai_search_window.py` | `on_keyboard` |
  | `gui2/utilities/sandhi_contraction_find_replace_gui.py` | `on_keyboard` |
  | `gui2/utilities/find_words_with_examples.py` | `on_keyboard` |
  | `db_tests/gui/main.py` | `on_keyboard` |

  The commented-out site in `db_tests/gui/add_hyphenations.py` was left alone.

  **Add BR-18 to `spec.md`'s BR list and to Phase 7's confirmation table**
  (done; the table now stands at 25 rows). Its evidence line is "press Ctrl+Q and the
  window actually closes" — "no error" is not evidence here.

- [x] **BR-19 (new) — `Control.page` RAISES when unmounted; it no longer reads
  `None`.** Found by the user's first launch, which crashed with
  `Pass1AddView(1753) Control must be added to the page first`.

  In 0.28 `page` was a plain attribute, `None` until mount. In 1.0 it is a
  property that walks up to the `Page` and raises `RuntimeError` if it never
  finds one (`flet/controls/base_control.py:298-313`). Two whole idioms in this
  codebase depended on the old behaviour:

  1. **Caching a view's page in a plain helper built from its constructor.**
     `DpdFields.__init__` did `self.page = self.ui.page` — and `DpdFields` is
     built inside `Pass1AddView.__init__`, so it raised before the view could
     finish. That is the reported crash. `TestsTabController.__init__` had the
     same line against its view.
  2. **Testing for mounting with `if control.page` / `control.page is None`.**
     13 sites. Each now raises the exact error it was written to prevent —
     **including the BR-13 guard this thread added two tasks ago**, which is
     why that fix was wrong as written.

  Fixes: `page_of()` and `is_mounted()` in `gui2/ui_utils.py` wrap the raise and
  return `None`/`False`; all 13 mount tests now use `is_mounted`. `DpdFields`
  and `TestsTabController` grew a lazy `page` property resolving through the
  view instead of caching — every reader runs after mount, so this is
  equivalent. The four parameterised updates from BR-17 now skip the refresh
  rather than assume a page.

  **New guard: `artifacts/check_page_reads.py`**, catching both shapes
  repo-wide. `check_premount_page.py` could not: it walks one control subclass
  at a time, and shape (1) lives in a *different* class while shape (2) reads
  someone else's attribute. Proven rather than assumed — run against `HEAD` it
  reports **16 hits** (3 cached, 13 mount tests); run against the working tree,
  **0**.

  **This is the third correction to the same assumption in this thread**, and
  the pattern is worth stating plainly for Phases 4–6: BR-17's fix was scoped by
  "which constructors read `self.page`", and that framing was too narrow twice
  over — first missing transitive reads inside the same class, now missing
  reads from other objects entirely. Anything that touches `.page` outside a
  handler needs checking, not just constructors.

  Add BR-19 to `spec.md` and to the Phase 7 table, which becomes 19 rows.

- [x] **BR-20 (new) — removed keywords beyond the button classes.** The user's
  second launch died on `PopupMenuItem.__init__() got an unexpected keyword
  argument 'text'`, on the Pass2Add tab.

  BR-7's task text said "check other button classes for `text=` at the same
  time", and that is exactly what was done — which is why this was missed.
  `PopupMenuItem` is not a button class. The real shape of the problem is
  *every* control that dropped or renamed *any* keyword, and there was no way
  to know which from the guide's tables.

  **The fix is a checker, not three edits** — `artifacts/check_flet_kwargs.py`.
  It walks every `ft.<Name>(...)` call and every `super().__init__(...)` in a
  class subclassing `ft.<Name>` (that second shape is how the `Dpd*` wrappers
  pass their styling, and a wrong keyword there breaks all 48 fields at once),
  then asks the **installed Flet** whether each keyword actually exists.

  1,309 constructions checked. Three were wrong, all now fixed:

  | Site | Was | Now |
  |---|---|---|
  | `pass2_add_view.py` ×2 | `PopupMenuItem(text=)` | `content=ft.Text(...)` |
  | `compound_type_tab_view.py` | `TextField(helper_text=)` | `helper=` |

  Note the asymmetry the checker caught and a sweep by hand would not:
  `Dropdown` **keeps** `helper_text`, `TextField` renamed it to `helper`. Three
  other `helper_text=` lines in the same file are on dropdowns and are correct
  as they stand.

  Self-tested rather than assumed: run against `HEAD` over five files it finds
  **11** removed keywords — the dropdown `on_change`es, the tab container's
  `tabs=`/`tab_content=`/`content=`/`on_click`, both `PopupMenuItem(text=)` and
  the `helper_text=`. Against the working tree, **0 of 1,309**.

  **This checker should have existed before Phase 3 started.** Every rename
  task in this plan was scoped from the migration guide's tables, and the guide
  is incomplete — AD#2 already says the wheel is the authority, but the plan
  only applied that rule to items it already suspected. Run this checker at the
  top of Phase 6, and again in Phase 7.

- [~] **BR-25 (new) — `expand` now beats `width` on a form field, so the pass
  views' dropdowns stretch across the whole row.** Found by measuring the
  user's 1.0 screenshot against `screenshots_before/07_pass2add.png` after they
  reported the fields looking "cramped".

  The measurement is the point here, because the obvious suspect was wrong.
  Field heights (57px), row pitch (63px), text insets and outline brightness
  are all **unchanged** from 0.28 — the border pass did not alter the geometry
  at all. One thing did change: the `pos` / `neg` / `verb` / `trans` /
  `plus_case` dropdowns were 665px wide and are now 1251px, filling the row.

  Cause: `DpdDropdown` and `DpdTextField` in `gui2/dpd_fields_classes.py` both
  pass `expand=True` **and** `width=700`, which contradict each other. 0.28 let
  `width` win for the dropdown and `expand` win for the text field; 1.0 lets
  `expand` win for both. Fix: drop `expand` from `DpdDropdown` only, so its
  `width=700` governs again. `DpdTextField` is left alone — it was already
  full-width in 0.28.
  → verify: against `screenshots_before/07_pass2add.png`, the dropdowns stop
    well short of the text fields' right edge again.

- [x] **BR-26 (new) — 1.0 pads a button's label more, so a fixed-width button
  wraps its label mid-word.** Reported from the Filter tab, where `Save`,
  `Rename` and `Delete` rendered as `Sav/e`, `Rena/me`, `Del/ete`.
  **Confirmed fixed by the user, 2026-09-17: all three now read on one line.**

  **Measured, not guessed.** In `screenshots_before/11_db.png` the three pills
  are exactly 80, 100 and 80 pixels wide — the widths the code asks for — and
  the labels fit on one line. The same widths are honoured in 1.0. So the width
  is not what changed; the room left for the label inside it is.

  Fix: drop `width` from those three `ft.Button`s so Material sizes each to its
  label. That reproduces 0.28's look (the pills already hugged their labels,
  which is why the numbers were 80/100/80 in the first place) and cannot be
  invalidated by the next change to Flet's button padding. Bumping the three
  numbers would have meant three new magic values with the same fragility.

  **The sweep is bounded and complete.** An AST pass over every `ft.Button` /
  `FilledButton` / `OutlinedButton` / `TextButton` in `gui2/` with a resolved
  width of 130 or less returns 11 sites: the three fixed here, six `Add` at
  width 100 in `sandhi_view.py`, and `Search` / `Clear` at width 120 in
  `translations_view.py`. `Add` is three characters at the width that wrapped
  six, and `Search` has 20 px more than `Rename` had, so neither is expected to
  wrap — left alone rather than pre-emptively changed.
  → verify: on the Filter tab, `Save`, `Rename` and `Delete` each read on one
    line. Then glance at the Sandhi tab's `Add` buttons and the Translations
    tab's `Search` / `Clear`, which the sweep predicts are fine.

- [~] Phase verification: launch and walk the entire behaviour catalogue.
  → verify: every entry behaves as described, or the deviation is recorded here
    with a cause. UI freezes are expected at this point — that is Phase 4.

  Superseded by the Phase 7 test round, which is the same exercise done once at
  the end rather than twice. Scoped honestly in the Phase 7 catalogue task —
  not a full per-binding walk, with what remains unobserved named there.

### Open issues from battle-testing — START THE NEXT SESSION HERE

Found by the user running the migrated app on 2026-09-17. Fixed already:
tab-order/focus (BR-21), the `PopupMenuItem` crash (BR-20), the launch crash
(BR-19), Ctrl+Q (BR-18). Since then: BR-22 and BR-24 fixed, BR-23 retested and
found not to be a defect, and BR-25 found by measuring the user's screenshot
against the baseline. All four are done in code and awaiting one visual pass.

- [~] **BR-22 — input fields render square; they were rounded in 0.28. The
  user wants them rounded.** This is the top priority: it affects every screen.

  **Done in code on 2026-09-17; awaiting the user's visual check.** What landed:

  - `field_border(color=None, width=1.0, radius=20)` in `gui2/ui_utils.py`,
    returning `ft.OutlineInputBorder`. Leaving `color` unset keeps the Material
    theme's per-state colours, which is what a `border_radius`-only field used
    to get. `FIELD_RADIUS = 20` is the codebase's existing convention (94 of the
    101 radius values were already 20).
  - **116** deprecated kwargs across **84** constructions in 20 files converted
    to `border=field_border(...)`. Not 135 — that count came from a flat grep
    and included 13 `border_radius=` on `Container`/`DataTable`, where the
    property is **not** deprecated. `artifacts/check_border_props.py` separates
    them by callee and is the authority; it now reports **0** deprecated kwargs
    on form fields.
  - **28** borderless `TextField`/`Dropdown` constructions given
    `border=field_border()`. The plan said 31; the real figure after excluding
    the `Dpd*` wrappers (which set their border in their own `__init__`) and
    `gui2/utilities/` (Phase 6) is 28. The two `SearchBar`s in that list were
    dropped: `SearchBar` is not a `FormFieldControl` in 1.0 and has no `border`
    — it takes `bar_shape`/`bar_border_side`, and was never part of BR-22.
  - **BR-16's red signals had to move too**, which the plan did not anticipate.
    `.border_color = RED` / `= None` at `tests_tab_view.py` and
    `dpd_fields_examples.py` now set `.border = field_border(color=RED)` and
    back to `field_border()`; `filter_component.py`'s spell-check border goes
    through a new `cell_border(colour)` so the red state keeps the cell's own
    square, 3px shape instead of reverting to the rounded default.
  - `border_width=0` on `pass2_auto_view.py`'s AI results field became
    `ft.NoInputBorder()` — `field_border` cannot express a widthless border,
    and "no border" was the evident intent. Judgement call; check it visually.

  Green after the pass: `ruff check`, `ruff format --check`, `uv run pyright`
  all clean on the 30 touched files; `just typecheck` 0 errors;
  `tests/gui2/` 284 passed; all 30 modules import.

  **Do not repeat the two wrong attempts.** First attempt blamed the deprecated
  `border_radius` property; second attempt fixed four fields that set an
  explicit border object — neither is what the user is looking at. The fields
  they named (`Add spelling`, the commentary `search for` / `which contains`,
  the DB presets dropdown, every Tests-tab field) **set no border properties at
  all**, so nothing in this codebase decides their corners: Flet's own default
  does, and it changed between versions. Both versions default to
  `border=None` on the Python side, so the difference is Dart-side and cannot
  be settled by reading the wheel.

  **The fix is to stop relying on the default.** 31 `TextField`/`Dropdown`
  constructions across 14 files carry no border setting; 80 others carry one.
  Give the 31 an explicit rounded border matching the codebase's existing
  convention (`border_radius=20`, or `ft.OutlineInputBorder(border_radius=20)`).

  **Do it as one pass with the 135 deprecated border properties below** — they
  are the same job. Converting every `border_radius=` / `border_color=` /
  `border_width=` to `border=ft.OutlineInputBorder(border_radius=..., side=...)`
  and giving the unstyled 31 the same treatment fixes the corners *and* silences
  every deprecation warning in one coherent change.
  → verify: against `artifacts/screenshots_before/`, screen by screen. This is
    a visual change; the screenshots are the only authority, and the user has
    already re-run the app three times for this one item. Compare before
    asking them again.

- [~] **BR-24 — the window still shows Flet's name and icon, not DPD's.**
  The three unknowns are now settled, and the premise was wrong: this was never
  a Flet default that changed.

  - `window.icon` **cannot work here.** Its own docstring in the installed
    wheel says "Has effect on Windows only" and "the file should have the
    `.ico` extension". The earlier attempt set an absolute `.png` on Linux, so
    it was inert twice over. The line is removed.
  - `ft.run(name=)` is **not** the window title — the wheel documents it as the
    "page/app name used in web URL path when applicable". `page.title` is the
    title, and it stays set.
  - **The taskbar name and icon come from the desktop entry, not from Flet.**
    `~/.local/share/applications/dpd-gui2.desktop` carries
    `StartupWMClass=flet`, and it is that entry which supplied `Name=dpd-gui2`
    and `Icon=…/dpd-logo-dark.svg` under 0.28. If 1.0's client reports a
    different WM_CLASS, the match breaks and the desktop falls back to the
    binary's own name and icon — exactly the symptom.

  **Confirmed and fixed 2026-09-17.** The user read the running window's class:
  `WM_CLASS(STRING) = "com.appveyor.flet", "Com.appveyor.flet"`. Under 0.28 it
  was plain `flet`, which is exactly what the desktop entry matched, so the
  rename broke it. `StartupWMClass=flet` → `StartupWMClass=com.appveyor.flet`
  in both copies: `gui2/linux/dpd-gui2.desktop` (the repo's template, the
  durable fix) and the installed `~/.local/share/applications/dpd-gui2.desktop`.
  **Scope change, user's call, same day:** having seen the title bar show
  "Digital Pāḷi Dictionary", the user asked for it removed. `page.title` is no
  longer set, so the window carries no title of its own. This does not affect
  the taskbar identity, which comes from the desktop entry.

  **Third scope change, same day: not setting the title was not enough.** The
  user's next launch showed `flet` in the title bar. An unset title is `None`,
  and the desktop client fills that with its own name rather than leaving the
  bar blank. `page.title = ""` is now set explicitly in `main()` — the empty
  string is the instruction to show nothing, where the absent value is an
  invitation for the client to choose one. Removing the line and setting it
  empty are not the same edit, which is the trap here.
  → verify: no name in the window's title bar, and the task switcher shows the
    DPD name and logo after the next launch.

- [x] **BR-23 — the example dialog on Pass2Add is no longer modal.**
  **Not a defect. Retested by the user on 2026-09-17: the eg dialog does not
  dismiss on an outside click. It is modal and always was.** The original
  report was a mis-observation, and the right call was to change nothing. Kept
  below because the reasoning is the reusable part.

  Investigated; **no code change made, and none was justified.**

  The installed wheel's docstring reads "Whether dialog can be dismissed/closed
  by clicking the area outside of it", which would make `modal` inverted in 1.0
  — but that docstring is wrong. Flet's own Dart control at tag `v1.0.0`
  (`packages/flet/lib/src/controls/alert_dialog.dart:113`) passes
  `barrierDismissible: !modal`, and `CupertinoAlertDialog`'s Python docstring
  still says "cannot be dismissed". So `modal=True` is the correct, unchanged
  spelling and `_eg_alert` is already written correctly.

  Flipping it would mean flipping all **18** `modal=True` dialogs in `gui2/` on
  a docstring that the shipped Dart contradicts. Not done.

  What is needed is one more observation, because the current one does not
  discriminate: does *any other* modal dialog also dismiss on an outside click
  (a Filter preset-name dialog, the Roots confirm dialog), or only the eg one?
  If only the eg one, the cause is local to that dialog — most likely its
  500×500 `Column` content leaving clickable page area inside the dialog's own
  route rather than the barrier being dismissible.
  → verify: open the eg dialog and click outside it; it must not dismiss. Then
    do the same with one other modal dialog and report whether it dismisses.

- [x] **Deprecated border properties** — done as part of BR-22. The real count
  was **116** on form fields, not 135: the original figure came from a flat
  grep that swept in 13 `border_radius=` on `Container` and `DataTable`, where
  the property is not deprecated and must stay.
  → verify: `artifacts/check_border_props.py` reports 0 on form fields. ✅

- [ ] **Open visual check left by BR-22: the focused border.** The fields that
  now carry `border=field_border(color=…)` — the dropdowns and several text
  fields — state an explicit `side`. The wheel says an explicit side "applies
  to the enabled state while the other states remain theme-resolved", which is
  what 0.28's `border_color` did too (it had a separate `focused_border_color`,
  which this codebase never used), so parity is *expected* rather than proven.
  Nobody has watched a field take focus yet.
  → verify: click into a dropdown and a coloured text field and confirm the
    focus ring still changes the way it did in 0.28. Cheap, and worth doing
    before it turns up as a mystery mid-battle-test.

**Not an issue:** `just gui` ran a `uv sync` once. That was the pin change
landing; verified not to recur.

### Pooled hand-off — what needs a human, and why

Everything checkable without a display has been checked. What is left cannot
be: it either fails silently or fails by looking wrong. Ordered so that a
failure early on saves doing the rest.

1. **Does it start, and does every tab have a body?** Launch `just gui`. Wait
   for the **"All tabs and tools ready."** snackbar — a window with a working
   first tab proves nothing, because the warm-up worker swallows exceptions
   (spec BR-17). Then open all 16 tabs and confirm each shows its view. The
   BR-14 failure mode is an *empty* tab with no error.
2. **Ctrl+Q quits** (BR-18). Silent no-op if wrong.
3. **Ctrl+S saves** on Tests or Roots. Silent no-op if wrong.
4. **PageUp/PageDown scroll on Pass2Add** — that tab only, index 7 (BR-4).
5. **Open the eg dialog on Pass2Add and, with it open**, press Alt+Left/Right
   and PageUp/PageDown; they must still work. Then dismiss it and confirm the
   global keys come back (BR-4 second half).
6. **Select from a dropdown** — `root_key` or `derivative` on a pass view, and
   the preset dropdown on Filter. Fires once, right value, right follow-on
   behaviour. Then type into an editable one and confirm it does *not* fire.
7. **Pass1Add: type a construction and blur it.** No error. Then the same in
   Pass2Add, where the compound-type suggestion should still appear (BR-13).
8. **Copy a lemma** (Add to DB, or the X button) and paste it elsewhere (BR-5).
9. **Open and dismiss every dialog and snackbar** in the catalogue.
10. **BR-16, visual only**: the four border-colour signals still go red and
    come back — invalid filter input, an example over 300 characters, a failing
    test row, and the book dropdown's grey border.
11. **Compare each screen against `artifacts/screenshots_before/`** for button
    labels and for spacing and borders.

Expect the window to freeze during slow actions. That is Phase 4's job, not a
Phase 3 defect.

**The border deprecation warnings are gone** — converting them was folded into
BR-22 once the user asked for the rounded corners back, since it is the same
edit in the same files. Superseded; the earlier `NOTICED — NOT TOUCHING` note
no longer applies.

---

## Phase 4 — Threading model

- [x] Port the instrumentation to the 1.0 dispatch boundary and re-run against
  the migrated build; compare to `artifacts/slow_handlers.md`.
  → verify: an updated log exists for 1.0.0 and the handlers that were slow
    before are still slow, proving the measurements are comparable.

  **Port done and verified headlessly; the live re-run needs the user.**

  **1.0 has one dispatch boundary where 0.28 had three.** The 0.28 version
  patched `Page.run_thread` plus the awaited branch of `Page.on_event_async`,
  because a handler reached user code by three routes there. In 1.0 all four
  handler shapes — plain sync, sync generator, coroutine, async generator — are
  invoked inside `BaseControl._trigger_event`
  (`flet/controls/base_control.py:453`), awaited from `Session.dispatch_event`
  (`flet/messaging/session.py:423`). Patching that one method covers
  everything, page-level events included, because `Page` is a `BaseControl`.
  `Page.run_thread` still exists (`flet/controls/page.py:899`) and is still
  patched, since gui2 launches its own background work through it.

  **One correction the port had to make to stay comparable.**
  `_trigger_event` also awaits `Session.after_event`, which flushes the UI
  patch — framework time, not handler time, and 0.28's sync route never
  included it. Timing `_trigger_event` verbatim would have inflated every row
  against `artifacts/slow_handlers.md`, and worst for exactly the handlers that
  touch the most controls. So `Session.after_event` is patched too, accumulating
  its own elapsed into a per-dispatch `ContextVar`, which is subtracted. A
  `ContextVar` rather than a global because `dispatch_event` runs in its own
  task, and generators call `after_event` once per `yield`, so the subtraction
  has to accumulate rather than assume one call.

  **Verified headlessly against all four 1.0 handler shapes**, one row each,
  correct handler name and definition site, durations matching the injected
  sleeps: sync 20.3 ms, coroutine 30.6 ms, sync generator 20.6 ms, async
  generator 30.8 ms, against 20/30/20/30. The two generator cases prove the
  subtraction: each injected 50 ms of fake `after_event` time twice, and both
  still land on their sleep. A control with no bound handler logs nothing.
  `ruff` and `pyright` clean.

  **New log path: `artifacts/handler_timing_1_0_0.csv`**, same seven-column
  header as the 0.28 log so the Phase 2c analysis compares directly. Kept
  separate rather than appended, so the 0.28 baseline cannot be contaminated.

  The plan's note below about exercising the four unmeasured shortlist items
  **can no longer be honoured on 0.28** — the branch is migrated, so those four
  will be measured on 1.0 only, with no before-picture. That is option (b) of
  the two the Phase 2c task offered, taken by circumstance rather than choice.

  **First 1.0 session captured, 2026-09-17 18:12–18:18: 367 invocations across
  6 files.** More rows than the 0.28 run's 213, but weighted differently and it
  does **not** cover what the conversion list needs — see the coverage gap
  below.

  | Handler | Route | n | median | max |
  |---|---|---:|---:|---:|
  | `App._initialize_db_in_background` | `run_thread` | 1 | 11695.5 | 11695.5 |
  | `App._warmup_in_background` | `run_thread` | 1 | 3353.0 | 3353.0 |
  | `FilterComponent._apply_filters` | `run_thread` | 5 | 248.4 | 1986.6 |
  | `CompoundTypeTabView._on_word_submit` | submit | 1 | 192.1 | 192.1 |
  | `FilterTabView._apply_filters_clicked` | submit | 3 | 41.2 | 74.6 |
  | `App._on_tab_activated` | change | 12 | 39.0 | 44.8 |
  | `App.on_keyboard` | keyboard | 188 | 0.5 | 15.2 |
  | cell tap / cell edit closures | tap / change | 149 | 0.4–3.3 | 5.3 |

  **Nothing on the UI thread is meaningfully over budget.** The three genuinely
  slow operations are all already on worker threads. The single exception is
  `_on_word_submit` at 192 ms against the 150 ms submit budget — 42 ms over, and
  `n=1`, so by this plan's own rule it is not yet measured.

  **Both background operations are faster than on 0.28**: database
  initialisation 11.7 s against 15.5 s, warm-up 3.35 s against 4.2 s. Not a
  like-for-like comparison (different machine state, one sample each), but it
  rules out a threading-model regression, which is what this task exists to
  check.

  **`App.on_keyboard` at n=188 is the strongest single result in the thread.**
  It is the handler BR-4 made `async def`, it is on the keystroke path with a
  50 ms budget, and its median is 0.5 ms with a 15.2 ms worst case. The awaited
  `scroll_to` costs nothing measurable.

  **Coverage gap — the conversion list cannot be built from this session.** The
  6 files are `main.py` (202), `filter_component.py` (154),
  `filter_tab_view.py` (4), `compound_type_tab_view.py` (2),
  `pass2_add_view.py` (1) and Flet's own dialog wrapper (4). The session was
  the Filter tab and the Compound Type tab. So the four shortlist items the
  0.28 run missed — the two TSV re-readers, the CST book search and the
  subprocess launches — are **still unexercised**, and the pass views' Sanskrit
  lookups and keystroke handlers have one row between them. A second session on
  the pass views is needed before the next task can be scoped.

  **Session 2 captured, 18:20–18:31 — the log now holds 700 invocations across
  15 files** and covers the field system and the pass views, which session 1
  did not. Medians over the whole 1.0 log, against the 0.28 figures from
  `slow_handlers.md`:

  | Handler | Class | n | median | max | 0.28 |
  |---|---|---:|---:|---:|---:|
  | `_initialize_db_in_background` | worker | 2 | 10975.4 | 11695.5 | 15531.5 |
  | `_warmup_in_background` | worker | 2 | 3631.6 | 3910.2 | 4230.6 |
  | `TranslationsView.search_clicked` | submit | 2 | 1754.3 | 1898.3 | 1736.3 |
  | `Pass2AddView._click_x_button` | click | 1 | 797.7 | 797.7 | — |
  | `Pass2AddView._click_add_to_db` | click | 1 | 610.2 | 610.2 | 496.0 |
  | `click_commentary_search` | submit | 3 | 312.7 | 321.9 | — |
  | `FilterComponent._apply_filters` | worker | 5 | 248.4 | 1986.6 | — |
  | `_click_search_dialog_ok` (CST book) | submit | 2 | 242.2 | 244.9 | **never measured** |
  | `CompoundTypeTabView._on_word_submit` | submit | 1 | 192.1 | 192.1 | — |
  | `_click_run_tests` | click | 4 | 151.7 | 158.9 | — |
  | `DpdMeaningField._handle_on_blur` | blur | 6 | 94.8 | 1091.3 | — |
  | `App.on_keyboard` | keystroke | 200+ | ~0.5 | 70.0 | 0.0 / 66.7 |

  **The translations search is the headline, and it is a non-regression.**
  1754 ms median on 1.0 against 1736 ms on 0.28 — within noise of each other,
  and the user's own words for it were *"as slow as it always was, not
  noticeably slower"*. That matters more than the number: this is the slowest
  thing in the app, it still runs on the UI thread, and the migration did not
  make it worse. It remains the top conversion candidate, now with n=2.

  **The CST book search finally has a measurement** — 242 ms median, n=2. It was
  on the reading-based shortlist and missed by both the 0.28 session and session
  1. At 242 ms against a 150 ms submit budget it is over, but by far less than
  reading the code suggested; parsing a book is evidently cheaper than feared.
  Re-measure with a large volume before converting.

  **`DpdMeaningField._handle_on_blur` is the one new discovery**: median 94.8 ms
  across 6 samples but a 1091 ms maximum. A fast median with a 10× tail on a
  blur handler is the shape that produces "it's usually fine but sometimes
  hangs" reports, and it is the relationship-detector path. Worth its own
  investigation in the conversion task.

  **Both background loads came in faster again** — database initialisation
  10.9 s against 15.5 s, warm-up 3.6 s against 4.2 s, now n=2 each.

  **Still unmeasured after two sessions:** the two TSV re-readers as such
  (`construction_focus` and `compound_type_blur` were caught at 72–74 ms, but
  the focus door on `phonetic` was not), and the four subprocess launches.

  **A save fired with no corresponding row change, and it is unresolved.** The
  user asked to confirm headword 90136 `vattayati` landed. It is there and
  complete — 28 populated columns including `meaning_1`, `sanskrit`,
  `construction`, `source_1`, `example_1`, `synonym` and `var_phonetic`, so a
  pass2 edit of a pass1 draft did save at some point. But its `created_at` is
  12:59:36 and its `updated_at` is `None`, while `_click_add_to_db` fired at
  18:29:37 in session 2 and the WAL was written at 18:29:36.57. `updated_at`
  carries `onupdate=func.now()` and `update_word_in_db` sets every column then
  commits, so an UPDATE that changed any value would have stamped it.

  The benign reading — and the likely one — is that session 2's save re-saved
  values identical to those already stored, so SQLAlchemy emitted no UPDATE at
  all. Session 2's log supports that: it shows the X button, a clone, and four
  test runs, which is a testing session rather than an editing one. The
  alternative, that a save silently wrote nothing, cannot be ruled out from
  here because both produce exactly this evidence. Left open deliberately
  rather than resolved by assumption; the user passed on digging further.

  **The db edits the user reported earlier were not in session 1's window.** The most recent
  headword writes are `updated_at` 2026-09-17 12:44 (an earlier, uninstrumented
  run) and no row was created or updated between 17:00 and now, so the
  instrumented session contained no database write. Their examples were checked
  anyway and are clean — bold tags balanced, diacritics and apostrophes intact,
  multi-line examples preserved, `source`/`sutta` pairs consistent, including
  two-example rows.

  **`artifacts/instrument_handlers.py` is deliberately untracked** (AD#4 —
  throwaway, never committed), so a fresh clone of this branch will not have
  it. If it is absent, rewrite it from AD#4: patch the event-dispatch path
  rather than wrapping bound handlers, because `gui2` builds its tabs lazily
  and startup-time wrapping only ever sees the first screen. It also still
  imports `flet.core.page`, which 1.0 moved — that import is the first thing
  the port has to fix.

  **The 0.28 sample it is being compared against is thin:** 213 invocations
  across 6 files, heavily weighted to Pass2Add, and 4 shortlist items were
  never exercised. Before trusting the "what is actually slow" ordering, spend
  one short session exercising the tabs the first pass missed. A conversion
  list built on an unexercised handler is a guess wearing a measurement's
  clothes.

- [x] Convert the slow handlers, slowest first. Per handler choose deliberately:
  thread-offload-with-result when the value is needed; fire-and-forget for
  background work; a yielding generator where the handler reports progress
  mid-execution. Record the choice and reason per handler.
  → verify: after each conversion, perform that action and confirm the window
    stays responsive throughout (draggable, another control clickable) and the
    end result matches the catalogue entry.

  **Scope set by the user, 2026-09-17: three items, not the whole list.** The
  four handlers in the 240–800 ms band (`_click_x_button`, `_click_add_to_db`,
  `click_commentary_search`, the CST book search) are explicit button presses
  where a brief pause reads as work rather than as a freeze — left alone
  deliberately, not overlooked.

  | Converted | How | Why this choice |
  |---|---|---|
  | `TranslationsView.search_clicked` | `async def` + `asyncio.to_thread` | Slowest action in the app at 1754 ms and the value is needed to render results, so offload-with-result. It already showed a `ProgressRing` that could never spin, because the search blocked the loop that would have animated it. |
  | `DpdMeaningField._handle_spell_check` | `async def` + `asyncio.to_thread` | 95 ms median but 1091 ms worst case, on every blur of `meaning_1`. Both its callers (`_handle_on_focus`, `_handle_on_blur`) became `async def` too; the external `on_blur_callback` stays synchronous. |
  | first build of a tab | `_on_tab_activated` → `async def`, placeholder is now a `ProgressRing`, build via `asyncio.to_thread` | ~1.6 s of unavoidable work, so it needs an indicator rather than a lower number. The empty `ft.Container` placeholder showed nothing at all. |
  | startup database load | indeterminate `ft.ProgressBar` above the tab bar | 11 s, the longest operation in the app, previously with nothing on screen to say so. Toggled by the existing worker; no change to the threading. |

  **Two traps this hit, both worth recording.**

  1. **The tab-build indicator needs a loop turn, not just an update.** Setting
     the placeholder and calling `page.update()` is not enough — the patch is
     queued and only flushed when the loop next runs, which without an
     intervening `await` is *after* the build it was meant to cover. The fix is
     `page.update()` then `await asyncio.sleep(0)` then the offload. A spinner
     that appears after the work finishes is worse than none.

  2. **`_on_tab_activated` had three direct synchronous callers** — the Alt+Left,
     Alt+Right and Alt+jump paths in `on_keyboard`. Making it `async def`
     turned each into a discarded coroutine, so tab switching by keyboard would
     have silently stopped building tabs. Caught by the **editor's** pyright,
     not by `uv run pyright`: `gui2/**` is excluded from the CLI's config, so
     `uv run pyright gui2/main.py` reports "0 errors" having analysed **0
     files** — a false pass. Verified with `--outputjson`
     (`filesAnalyzed: 0`). For `gui2/`, the real gates are `ruff`, the test
     suite, an import check, and the editor's own language server.

  Green after the pass: `ruff check` and `ruff format --check` clean on all
  five touched files, all five modules import, `tests/gui2/` 284 passed,
  `uv run pytest tests/` 1886 passed / 12 deselected, `just typecheck` 0 errors.

- [x] Audit the pre-existing concurrency: the three `page.run_thread` launches
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

  **Reading half done; the live exercise is owed and needs a human.** Done now
  rather than after the conversions, because none of it depends on the timings.

  The inventory is smaller than the task text implies — 8 lock objects, 4
  `run_thread` launches, 1 raw `threading.Thread`:

  | Site | Kind | Calls `update()` from the worker? |
  |---|---|---|
  | `main.py:302,432` `_initialize_db_in_background` | `run_thread` | yes — `show_global_snackbar` |
  | `main.py:433` `_warmup_in_background` | `run_thread` | yes — `_ensure_tab_built` → `page.update()`, plus a snackbar |
  | `filter_component.py:238` `_apply_filters` | `run_thread` | yes — snackbars and the table rebuild |
  | `database_manager.py:671` `_detector_rebuild_worker` | raw `threading.Thread` | **no** |
  | `toolkit.py:46`, `main.py:39` (`RLock`); `database_manager.py:49,103`, `filter_component.py:129`, `pass1_file_manager.py:19`, `pass1_auto_controller.py:33` (`Lock`) | plain locks | n/a |

  **The task's stated risk does not materialise.** It says a raw
  `threading.Thread` does not re-establish page context, so "its `update()`
  calls are the risk, not its locks". The one raw thread in the codebase,
  `_detector_rebuild_worker`, touches no control at all: it opens its own
  session, builds a `RelationshipDetector`, swaps it into an attribute, and
  returns. Nothing to fix. Its debounce and coalescing are pure Python and
  unaffected by the Flet version.

  **`run_thread` still re-establishes context in 1.0**, confirmed in the wheel:
  `Page.run_thread` wraps the handler in `__context_wrapper`, which sets the
  `_context_page` ContextVar inside the executor thread
  (`flet/controls/page.py:894`) before calling it. So the three `run_thread`
  workers resolve their page correctly, and BR-19's raising `.page` property is
  not reached from them.

  **The real 1.0 question is cross-thread delivery, and reading cannot settle
  it.** A worker's `update()` goes `Page.update` → `Session.patch_control` →
  `FletSocketServer.send_message`, which ends in
  `asyncio.Queue.put_nowait` on a queue owned by the event loop
  (`flet/messaging/flet_socket_server.py:67,445`). `put_nowait` is not
  thread-safe: it wakes a waiting getter through `call_soon`, which from
  another thread is not guaranteed to wake an idle loop. The failure mode is
  therefore **a late update, not a lost one** — the patch sits in the queue
  until the loop next wakes for any reason, typically the user's next click. It
  would read as "the snackbar appears when I click something" rather than as an
  error, which is why it gets its own observation below.

  Desktop confirmed as the socket transport: `ft.run` takes the
  `__run_socket_server` branch unless `FLET_DART_BRIDGE_PORT` is set for an
  embedded runtime (`flet/app.py:267-280`), which this app does not set.

  `start_dpd_server()` at `main.py:453` is a FastAPI server started after the
  UI has painted; it is not a Flet worker and nothing about it changed with the
  pin.

  → live verify, added by this audit: at cold start, the
    **"Database loaded." and "All tabs and tools ready." snackbars must appear
    on their own**, without clicking anything. If they only appear on the next
    click, cross-thread delivery is the cause and it applies equally to the
    filter worker's results.

  ✅ **Cross-thread delivery works, and the timing log proves it without
  needing anyone to have watched.** The user reported not seeing the two
  snackbars, which looked like a confirmation of the risk above. It is not.
  Every `SnackBar` gets an `on_dismiss` wrapper from Flet
  (`BasePage._wrap_dialog_on_dismiss`), so a snackbar that renders and expires
  leaves its own row in the log — and there are four of them, each landing
  ~2.55 s after the worker that raised it, against a 2000 ms snackbar duration:

  | Worker finished | SnackBar dismissed | Gap |
  |---|---|---|
  | `_warmup_in_background` 18:12:12.104 | 18:12:14.749 | 2.6 s |
  | `_initialize_db_in_background` 18:12:20.444 | 18:12:22.998 | 2.55 s |

  So both snackbars were painted from their worker thread, on their own,
  promptly, and dismissed themselves on schedule. The `asyncio.Queue`
  thread-safety concern is real in the abstract but does not bite here — the
  loop is busy enough that a queued patch is picked up immediately. Nothing to
  fix, and **the user simply missed a 2-second message during an 11-second
  load.**

  This also closes BR-17's outstanding evidence gate by a route nobody
  planned: "All tabs and tools ready." fires only when every one of the 16
  views has been built without raising, and the log shows it fired.

- [x] Audit the non-database blocking: the 4 subprocess launches to external
  applications, the kill-and-restart sequence with its 3-second and 2-second
  sleeps in `gui2/global_tab_view.py`, and the retry sleeps in
  `gui2/pass1_auto_controller.py`.
  → verify: trigger each external-application launch and confirm the UI does not
    freeze and the external application opens.

  **Audited by reading; nothing converted, because the user's conversion scope
  was three named items and none of these is among them.** Recorded so the
  decision is visible rather than implied.

  | Site | Blocking work | Verdict |
  |---|---|---|
  | `_handle_open_test_file`, `_click_edit_compound_types`, `_click_edit_phonetic_changes`, `tests_tab_controller` / `test_manager` file opens | `subprocess.Popen` | **Fine as they are.** `Popen` does not wait; it returns as soon as the child is spawned. There is nothing to offload. |
  | `ai_search_window` launch | `subprocess.Popen` | Same. |
  | **`_click_update_anki`** (`global_tab_view.py:116`) | `pkill`, **`time.sleep(3)`**, `pgrep`, optional **`time.sleep(2)`**, then a full Anki export in-process | **The worst blocker in the app, and worse than the numbers suggest.** At least 3 s of deliberate sleep plus an entire export, all on the event loop. It calls `_update_message` five times to narrate its progress and **not one of those messages can paint**, because the loop that would paint them is the loop being slept on. The user sees a frozen window and then, at the end, only the last message. |
  | `_click_backup_quit` | TSV backup, then awaits `window.close()` | Blocking, but it ends in quitting the app, so responsiveness during it is moot. |
  | `send_prompt` retry sleeps (`pass1_auto_controller.py:424,431`) | up to 2 × `time.sleep(1.0)` | **Already off the loop** — reached from the Pass1Auto worker, not from a handler. Leave. |

  **Approved by the user and converted, 2026-09-17** — explicitly so the
  message output is visible while it works and at the end. `_click_update_anki`
  is now `async def`: both `time.sleep`s became `await asyncio.sleep`, both
  `subprocess.run` calls and `anki_updater_main()` went to `asyncio.to_thread`,
  and the `subprocess.Popen` restart was left alone because it does not wait.

  **A queued message is not a shown message**, which is the same trap the tab
  spinner hit. `_update_message` only calls `page.update()`, and that queues a
  patch — so a message set immediately before a blocking step is flushed after
  it. Every report now goes through a new `_say()` that sets the message and
  then awaits a loop turn. The awaits that follow would mostly have flushed it
  anyway, but relying on that would make each message's visibility depend on
  whatever happens to come next, which is exactly how this regresses silently.

  The other four subprocess sites and the retry sleeps needed nothing, per the
  table above.

  `NOTICED — NOT TOUCHING:` `_click_update_anki` also imports `time` inside the
  function body twice over, and `send_prompt` imports `time` inside itself with
  a stale "Add at top if not present" comment. Unrelated to the migration.

- [x] Phase verification: re-run the instrumentation against the spec's
  responsiveness table.
  → verify: two things, and the second is the gate.
    **(a)** Median and sample count per handler by class; no handler exceeds its
    class threshold. A handler measured once is not measured.
    **(b)** **The window never stops responding on any action.** Walk every
    long-running action — AI calls, book processing, external application
    launches, filter application, detector rebuild — and during each one drag
    the window and click another control. Both must work, and the progress
    indicator must visibly move.

  ✅ Confirmed by the user, 2026-09-17: the translations search, the tab
  spinner, the startup progress bar and the Anki update all behave, with the
  Anki messages now appearing as the work happens rather than only at the end.

### Phase 4 review — two independent reviewers, dispositions

Both reviewers answered the same six questions. Four came back clean from both.
Of the three findings raised, **one was rejected on evidence, two were applied.**

**REJECTED — "`_ensure_tab_built` runs `page.update()` on a thread with no page
context."** Reviewer 1 recommended splitting the offload so only `self._view()`
runs off-loop. The premise is wrong, and it matters because the same wrong
premise would justify churn anywhere `to_thread` is used:

`asyncio.to_thread` **does** propagate context — CPython implements it as
`ctx = contextvars.copy_context()` then `ctx.run(func, ...)` in the executor.
Only a bare `threading.Thread` loses it. Verified rather than argued:

```
to_thread sees: PAGE-OBJ  | thread: asyncio_0
bare Thread sees: None
```

So `_context_page` reaches the worker and `page.update()` resolves correctly.
The residual concern — a non-loop thread reaching `session.patch_control` — is
pre-existing, identical to what `_warmup_in_background` has always done, and
already **empirically disproved** by this phase's own concurrency audit (the
startup snackbars painted from their worker thread and dismissed on schedule).
Reviewer 2 reached the same conclusion independently. No change made.

**APPLIED — the border colour assumed a dark theme that was never stated.**
Reviewer 1's strongest finding. `FIELD_BORDER_COLOUR` is `GREY_800`, measured
off the 0.28 screenshots — but `gui2/main.py` never set `theme_mode`, so it
followed the system. On a light-themed desktop ~86 fields would have drawn a
near-black border on a pale ground.

`page.theme_mode = ft.ThemeMode.DARK` is now set. That is the established
sibling pattern, not an invention: `db_tests/gui/main.py:30` and both
`gui2/utilities/` scripts already state it; `gui2` was the only consumer that
did not. Reviewer 2 judged the risk tolerable; reviewer 1 was right that it
should be decided rather than left implicit.

**APPLIED — two comment guards, both against silent failures.**
- Ctrl+S calls `_on_save_changes` / `_save_changes_clicked` synchronously. Both
  are `def` today; if either is ever made `async def` the call becomes a
  discarded coroutine and Ctrl+S stops saving with no error — which this exact
  path already did once, under BR-14. Noted at the call site.
- `search_clicked` has no `await asyncio.sleep(0)` before its offload, unlike
  the tab-build path. It does not need one — awaiting `to_thread` itself yields
  the turn that flushes the progress ring — and the comment now says so, since
  the asymmetry otherwise reads as an oversight.

**CLOSED — the save that left no trace.** Both reviewers settled it as benign,
and the ORM semantics are decisive: `updated_at` carries `onupdate=func.now()`,
which fires only when an UPDATE actually executes, and `update_word_in_db`
copies every field then commits — so identical values mean zero dirty columns,
no UPDATE, no stamp. `updated_at IS NULL` therefore means "no UPDATE has ever
been emitted for this row", not "a write was lost". Row 90136 was born complete
in one INSERT at 12:59:36; session 2's press re-saved identical values.

One correction to reviewer 2's version: it attributes the 18:29:36.57 WAL write
to the preceding `_click_run_tests`. The arithmetic says otherwise —
`_click_add_to_db` is logged at completion (18:29:37.170) having taken 610.2 ms,
so it *started* at 18:29:36.56, which is the WAL write to the millisecond. The
save did write something, just not to that headword row (`mark_corpus_stale`
and the lookup sync both write). The conclusion is unchanged and benign.

The discriminator, if it is ever worth being certain: change one field, save,
and confirm the timestamp moves.

**NOT DONE, reported instead — reviewer 2's extra findings.** Both are real and
both are outside the conversion scope the user set:
- `_click_add_to_db` (`pass2_add_view.py:803-810`) still calls
  `check_sentence()` synchronously on the event loop — the same 1.1 s tail this
  phase offloaded for the meaning field, on the save path.
- `request_dpd_server()` below it is a synchronous HTTP call on the loop.

**NOT DONE, a decision for the user — the pyright false pass.** `uv run pyright
gui2/main.py` reports "0 errors" having analysed **0 files**. Reviewer 2's
suggestion is a guard that fails when `filesAnalyzed == 0`. Worth doing, but it
changes a repo-wide gate rather than this migration, so it is not taken here.

`NOTICED — NOT TOUCHING:` the 30 `color=ft.Colors.GREY_800` arguments in
`compound_type_tab_view.py` are now redundant, since that is the default.
Harmless, and removing them is a cosmetic rename under AD#8.

---

## Phase 5 — Automatic updates audit

- [x] Find every remaining place a control is refreshed before it is attached.
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

  ✅ **Zero call sites changed.** New guard
  `artifacts/check_premount_update.py`, the sibling of `check_premount_page.py`:
  it walks the call graph from every control subclass's `__init__` and reports
  any `update()` it reaches. First run printed **6**, all six false positives on
  inspection, and the scanner was tightened rather than the code:

  | Site | Why it is safe |
  |---|---|
  | `compound_type_tab_view.py:88,109` | inside an `on_select` lambda — bound in the constructor, run after mount |
  | `filter_tab_view.py:289,382`, `pass1_add_view.py:437`, `pass2_add_view.py:678` | `target` is `page or page_of(self)`, BR-17's own fix pattern, so the receiver is the `Page` |

  So the scanner now skips nested functions and lambdas, and recognises the
  `page or page_of(self)` alias. Its sensitivity is proved rather than assumed:
  a synthetic `__init__ -> _refresh -> self._f.update()` is still reported.

  The two `_add` shadow-field updates outside constructor scope were re-checked
  against the live lists rather than the spec's prose. `dpd_fields.py:1586`
  carries the Phase 3 `is_mounted` guard; `:940` (`phonetic_add_field`) needs
  none — `'phonetic' in PASS1_FIELDS` is `False`, so it is unreachable on the
  one screen where the `_add` fields are unmounted, and Pass2Add mounts them
  all (`add_to_ui(..., include_add_fields=True)`).

  Launching and walking every screen is owed and needs a human; it is pooled
  with the Phase 7 catalogue walk.

- [x] **BR-13 second case:** `update()` also raises on a frozen control
  (`"Frozen control cannot be updated."`). New in 1.0, not in the guide, not
  caught by either review.
  → verify: no `RuntimeError` mentioning a frozen control during a full walk of
    the catalogue.

  ✅ **Zero sites, settled by provenance rather than by walking the catalogue.**
  `_frozen` is only ever set in two places in the installed wheel, and both are
  inside `flet/components/` — the declarative components API
  (`component.py:149,164` marks a rendered subtree frozen, and
  `hooks/use_dialog.py:107` patches a dialog frozen). Nothing else in Flet sets
  it.

  This codebase uses the imperative API exclusively: a grep over `gui2/` and
  `db_tests/gui/` for `ft.component`, `@component`, `ft.Component`,
  `from flet.components`, `use_state` and `use_dialog` returns **zero**. No
  control here can acquire `_frozen`, so the second case cannot arise. That is
  stronger evidence than a clean walk would be, which is why the walk is not
  the verification.

- [x] Find every handler that refreshes mid-execution to show progress; convert
  to yielding generators.
  → verify: perform each such action and watch the screen — the progress
    indicator visibly changes *during* the operation, not only at the end.

  ✅ **Six handlers, all converted.** 1.0 does support the generator form the
  task names — `BaseControl._trigger_event` has a `isgeneratorfunction` branch
  that flushes the patch and `await asyncio.sleep(0)`s on every `yield` — but
  the pattern used is Phase 4's `async def` + `asyncio.to_thread`, which the
  user has already confirmed working in this app. It satisfies the same verify
  line and additionally keeps the window responsive, where a generator would
  paint the message and then freeze for the duration.

  | Handler | Message that never painted | Now |
  |---|---|---|
  | `global_tab_view._click_backup_quit` | "Running database backup..." | `_say` + `to_thread(backup_dpd_headwords_and_roots)` |
  | `global_tab_view._click_update_inflections` | "Updating inflections..." | `async def`, `_say`, three `to_thread` calls |
  | `pass2_add_view._click_update_sandhi` — menu item **"Update Speech Marks"** | "updating speech marks... please wait..." | `async def` + `to_thread(regenerate_from_db)` |
  | `pass2_add_view._click_update_with_ai` — menu item **"AiAutofill"** | "Requesting AI update for …" | `async def` + `to_thread(process_single_headword_from_view)` |
  | `ai_search_window._handle_submit` | "Getting response..." | `async def` + `to_thread(ai_manager.request)` |
  | `tests_tab_controller.handle_run_tests_clicked` | three: loading tests / integrity check / loading database | `async def`; `load_tests` and `load_db` to `to_thread` |

  Two decisions inside that table worth recording:

  - **No `_say` helper was added to `pass2_add_view`.** Where the message and
    the `await to_thread(...)` are adjacent, awaiting the offload is itself the
    suspension that flushes the patch — the same reasoning already written into
    `translations_view.search_clicked`. A comment at the sandhi call site says
    so. `global_tab_view` keeps using its existing `_say`, that being the file's
    own idiom.
  - **The integrity check is not offloaded.** `integrity_check` writes the
    failing test's name into the view, and a worker thread must not touch
    controls, so it keeps running on the loop with a bare
    `await asyncio.sleep(0)` in front of it to flush the message. The rest of
    the tests run loop (`_run_next_test_from_generator`) is untouched.

  **Caller audit, per the Phase 4 lesson that `gui2/` has no type checker to
  catch an async mistake:** all six are bound only (`on_click=` / `on_submit=`)
  and none is called directly anywhere in `gui2/`. `check_unawaited.py` reports
  0.

  **User's test, 2026-09-17.** The Ask AI window is confirmed working. Two of
  the menu items were named here by their method rather than by the label the
  code renders — they are **"Update Speech Marks"** and **"AiAutofill"**, and
  the table above is corrected. Three results need recording:

  - **Tests tab — only "loading database..." was seen.** Not a defect, and
    measured rather than assumed: `load_tests` takes **13 ms** (549 tests) and
    `integrity_check` **1 ms**, against roughly 15 s for `load_db`. The first
    two messages do paint; they are simply on screen for a few milliseconds.
    Nothing to fix. (Whether those two steps deserve a message at all is a
    pre-existing design question — `NOTICED — NOT TOUCHING`.)

  - **Update inflections prints `Error: tic() not called before toc()`.**
    **PRE-EXISTING — NOT CAUSED BY THIS THREAD.** `InflectionsManager.run()`
    ends with `pr.toc()`, but `pr.tic()` is only ever called by that module's
    own `main()` (`db/inflections/generate_inflection_tables.py:290,295`). Any
    caller that invokes `run()` directly hits it, and `git show
    main:gui2/global_tab_view.py` shows the handler called `run()` directly on
    `main` too. Console noise only; the inflections work itself completed.

  - **Backup and quit failed at `committing changes to GitHub`** with
    `Unable to create .git/index.lock: File exists`. **PRE-EXISTING —
    NOT CAUSED BY THIS THREAD**, and it is the ⚠️ DRIFT already recorded
    against the Phase 3 backup task: `backup_dpd_headwords_and_roots` calls
    `git_commit` unconditionally. The TSVs were written correctly; only the
    commit failed, on a transient lock from another git process. No
    `.git/index.lock` remains.

    **It left three files staged in the shared tree** —
    `db/backup_tsv/dpd_headwords_part_001..003.tsv` are in the index, because
    `git_commit` ran `git add` before the hook rejected the commit. Reported to
    the user; this thread does not run git and must not unstage them. Had the
    lock not intervened, a `pali update` commit would have landed on the
    `flet-1-0` migration branch, which is exactly what the Phase 3 drift note
    predicted.

- [x] Review the 372 manual refresh calls. Most are now harmless no-ops; leave
  them. Remove one only where it is provably wrong. **Do not do a cleanup
  sweep** — this is a migration, not a refactor.
  → verify: state here how many refresh calls changed and why each had to. If
    the answer is "none beyond the two categories above", that is correct.

  ✅ **None beyond the two categories above.** No `update()` call was added,
  removed or moved by this phase; the six conversions changed *when* the loop
  gets a turn, not what is refreshed.

  One thing was checked and deliberately left alone. 15 live sites still close a
  dialog with the 0.28 idiom `dialog.open = False` + `page.update()` rather than
  `pop_dialog()`, which looked at first like a missed BR-8 conversion. It is
  not: `BasePage.pop_dialog` is literally `dialog.open = False; dialog.update()`,
  and the dialog lives in `page._dialogs`, so the existing idiom is equivalent.
  `NOTICED — NOT TOUCHING`.

**Phase 5 verification.** `uv run pytest tests/` **1886 passed, 12 deselected**;
`tests/gui2/` **284 passed**; `just typecheck` **0 errors**; `ruff check` and
`ruff format` clean on all four touched files plus the new guard; all four
modules import. All four guard scripts exit 0 —
`check_unawaited` 0, `check_premount_update` 0, `check_premount_page` 0,
`check_self_page` 0 breaks / 16 safe.

---

## Phase 6 — The other Flet consumers

`db_tests/gui/` and the standalone utilities. No service rewrites: nothing here
constructs a `FilePicker`, so BR-9 has no sites.

**Partly pulled forward into Phase 3, not by choice.** The renames are
repo-wide sweeps and `just typecheck` is repo-wide, so `db_tests/gui/` could
not be left on the old API without leaving the tree red. What is already done:

- **The mechanical renames**, everywhere: `ft.run`, `ft.Button`, the `Padding`
  and `Alignment` constants, `show_dialog`/`pop_dialog`, and BR-18's awaited
  `window.close()`.
- **`db_tests/gui/` typing.** 1.0 made `Event` generic *and invariant*, so
  every handler annotated `ft.ControlEvent` became unassignable to the control
  that binds it. 15 pyright errors, all new with the pin bump, all fixed by
  annotating the real type (`ft.Event[ft.ListTile]`,
  `ft.Event[ft.TextButton]`, `ft.Event[ft.Button]`) rather than by widening or
  ignoring. That also fixed the `e.control.title` access, which only failed
  because the event's control type was unknown. `uv run pyright db_tests/gui/`
  is now clean, and `just typecheck` reports 0 errors.
What Phase 6 still owes: confirming each tool still starts on 1.0.

- [x] Migrate the 7 data-integrity GUI helpers (`db_tests/gui/main.py` plus the
  taddhita, su/dur, negative-compound, two antonym and hyphenation tools).
  Entry point at `db_tests/gui/main.py:169`; otherwise the same renames.
  **None of these needs BR-17 work** — their classes are plain, not controls.
  → verify: the module imports, no 0.28-only API survives anywhere in the tree,
    and its entry point resolves. Then launch it and confirm it opens, displays
    data, and its primary action works — that half needs a human.

- [x] Migrate the 2 standalone utilities under `gui2/utilities/` and
  `gui2/test_app.py`.
  → verify: each module imports and its entry point resolves; then each
    launches.

  ✅ Both tasks verified together by a new guard,
  `artifacts/check_phase6.py`, which covers all 10 files in one pass and
  **exits 0**. Three checks:

  | Check | Result |
  |---|---|
  | dead 0.28 API — 16 removed spellings, across all 10 files | clean |
  | imports | clean |
  | entry points resolve to a callable | clean |

  The entry-point row is the plan's own list read back: `db_tests.gui.main.main`,
  `gui2.test_app.main`, `gui2.utilities.find_words_with_examples.run_gui`,
  `gui2.utilities.sandhi_contraction_find_replace_gui.main`. Note
  `find_words_with_examples` is `run_gui`, not `main` — the plan's prose said
  "the same renames" and an executor assuming `main` would have got a false
  negative.

  **`db_tests/gui/main.py` calls `ft.run()` at module level**, so importing it
  opens a window. It is compiled and AST-resolved instead, and the guard says
  so in a comment rather than silently skipping it.

  **Sensitivity proved, not assumed.** All 16 dead-API patterns were fed a
  known-bad line and all 16 fired; the 9 correct 1.0 spellings — including
  `ft.border.BorderSide`, which must survive per BR-2 — produced zero false
  positives. A sweep that finds nothing is worth nothing until it is shown it
  can find something.

  `ruff check`, `ruff format` and `pyright` clean on the new guard.

  **Still owed and it genuinely needs a human:** actually launching each tool
  and using it. The static pass proves no removed API survives and every module
  loads; it cannot prove a window renders. Carried into the Phase 7 hand-off
  rather than claimed here.

---

## Phase 7 — Verification and handover

- [x] Regenerate the wiring inventory and diff against
  `artifacts/wiring_baseline.txt`; save as `artifacts/wiring_diff.md`.
  → verify: every diff line annotated as an intended rename (button class, tab
    label, dropdown handler), a structural improvement named in
    `artifacts/improvements.md`, or a deliberate change with a reason. **Zero
    unexplained differences.** A handler that vanished without explanation is a
    migration bug, not diff noise.

    **On the dropdowns, expect this exact split** — an earlier draft said "11
    lines become `on_select`", which would make an executor flag three correct
    rows. **8 rows become `on_select`**: 7 direct `ft.Dropdown` sites plus the
    `DpdDropdown` wrapper's `super().__init__` row. (This line previously said
    "8 direct sites plus the wrapper", i.e. 9 — that was an off-by-one against
    the inventory, corrected from the measured diff.) And **3 rows keep
    `on_change`** (`dpd_fields.py:153`, `:199`, `:337`) because that is the
    wrapper's own parameter name, shared with `FieldConfig.on_change` across
    all 50 field definitions. The comment in `dpd_fields_classes.py` says why.

    The baseline is the frozen 0.28 record and carries 14 rows from a
    directory later removed from scope. Filter those out of both sides before
    diffing, so the comparison is 449 against 449.

  ✅ **Zero unexplained differences**, written up in `artifacts/wiring_diff.md`.
  449 in-scope bindings before, 448 after.

  The diff is not read by eye. `artifacts/diff_wiring.py` classifies every
  difference against a table of intended renames and exits non-zero while any
  is unaccounted for. It strips line numbers first — every file in scope moved
  lines, so a line-sensitive diff would be all noise.

  | Count | Reason |
  |---:|---|
  | 143 | BR-7 — `ft.ElevatedButton` → `ft.Button` |
  | 8 | BR-1 — `Dropdown.on_change` → `on_select` |
  | 3 | BR-8 — `page.close(dlg)` → `page.pop_dialog()` |
  | 1 | BR-14 — the `Tabs` `on_click` binding, deliberately removed |

  **The 449→448 drop is that last row and nothing else.** The script models it
  as an expected *removal*, not a rename: a surviving binding is reported as
  `EXPECTED TO BE REMOVED but still bound` and fails. Absence is the pass.

  The BR-8 rows show a changed *callable*, not just a changed keyword, because
  `pop_dialog()` takes no argument where `page.close(dlg)` named one.

  **The dropdown prediction held, but this plan's own prose was off by one.**
  The verify line above said "8 direct sites plus the wrapper" (9). The
  inventory says **7 direct plus the wrapper = 8**, and exactly the 3 predicted
  rows keep `on_change` (`dpd_fields.py:153`, `:199`, `:337`). The verify line
  is corrected above, from the measurement rather than from the prose.

- [x] Audit `artifacts/improvements.md` against the actual diff.
  → verify: every improvement in the log is present in the code, and every
    structural change in the code is in the log. A restructure that is not
    logged is a review finding — it is the thing a reviewer cannot tell apart
    from a migration bug. Re-check each logged row's evidence column still
    holds after the full walk.

  ✅ Both directions checked, and the second direction found something.

  **Log → code.** Both logged improvements are present and in use:
  `field_border()` in `gui2/ui_utils.py`, **117 call sites**; `cell_border()`
  in `gui2/filter_component.py`, 4 call sites including the two spell-check
  branches its evidence column depends on. Each evidence column still holds.

  **Code → log: three shared helpers were missing from the log.** Every added
  top-level `def` in `gui2/` and `db_tests/` was diffed against `main`, which
  turned up `page_of`, `is_mounted` and `request_focus` in `gui2/ui_utils.py` —
  none of them mentioned anywhere in `improvements.md`.

  They are **correctly** absent from the taken-improvements table: each *is* a
  BR fix rather than an improvement on top of one (BR-19 for the first two,
  BR-21 for `request_focus`), the same disposition as C1. But a reviewer
  meeting a new shared helper with 51 call sites will ask which it is, and the
  log is the file that is supposed to answer that without them going looking.

  So `improvements.md` gains a **"Shared helpers that are not improvements"**
  section naming all three, their call counts, the BR item each implements, and
  why no rollback hunk is owed for them — reverting one reinstates a broken
  1.0 idiom rather than restoring 0.28 behaviour.

- [~] Walk the entire behaviour catalogue in the migrated app, ticking each
  screen off in the catalogue file itself.
  → verify: every entry confirmed, or the deviation recorded with a cause.

  **Not done as a catalogue walk, and not claimed as one.** The user's test
  round covered 15 behaviours plus 4 retests and the daily editing they do
  anyway — which is broader evidence than a tick-list on some screens and
  narrower on others. A screen-by-screen walk of all 415 catalogued bindings was
  not run, so this stays `[~]`.

  What that leaves genuinely unobserved is small and named: the three BR-16
  border signals, the BR-22 focused ring, and the per-field dropdown behaviours
  in catalogue §1.3 beyond the two the round exercised. Everything else in the
  catalogue is either covered by the round or is a field handler whose wiring
  the diff proves unchanged.

  ⏸️ Original note: **needs the running app.** Nothing
  here is checkable statically: the point of the walk is watching each screen
  behave. The static half of what it would catch is already covered by the
  wiring diff (no handler silently dropped or rebound) and the BR sweep table
  below (no removed 1.0 API surviving anywhere).

- [~] Confirm each of BR-1 to BR-26 individually in the running app and record
  the evidence here.
  → verify: a 26-row table, each row naming the observation that confirms it.
    BR-9 is dropped (no sites in scope) — mark it so rather
    than leaving a blank. BR-23 is closed as not-a-defect, so its row records
    the retest, not a fix. BR-18 needs Ctrl+Q actually quitting, BR-21 needs
    focus actually moving to the next field; neither shows an error when broken.
    "No error on launch" is not an observation for the silent failures (BR-1,
    BR-4, BR-14's Ctrl+S path, BR-16) — those need someone to watch the
    behaviour happen. BR-15 is a zero-site sweep, confirmed by the grep.

  🔶 **Static half done, 26 rows below. 11 rows needed the running app** and
  are marked 👁. The verify line's own warning is the reason: for the silent
  failures, code evidence is necessary and not sufficient.

  ✅ **The user's test round settled 10 of those 11** — see *Phase 7 test
  round* above for the numbered results. Confirmed there: BR-1 (#3), BR-4 (#4),
  BR-8 and BR-17 (#1, #2), BR-14 (#2, #6), BR-18 (#7), BR-21 (#8, with residual
  cases the user is taking), BR-22 (#10 plus the red-border retest), BR-24
  (#13), BR-25 (#11, after BR-28), BR-26 (#12).

  **The one still open is BR-16**, and only partly: 1 of its 4 border signals
  is confirmed. See the BR-16 task in Phase 3.

  Two of these rows only passed *because* the round ran: #11 became BR-28, and
  the Test button's border became BR-27 — which turned out to be ~60 dead
  validation messages, not one missing border. A 👁 row is not a formality.

  **One sweep caveat that would otherwise produce false greens.**
  `gui2/build/site-packages/` holds a vendored copy of **Flet 0.28** as a build
  artifact. A naive `grep` for removed API across `gui2/` returns 69 hits for
  `ft.app(` and 37 for `ElevatedButton` — every one inside that vendored copy.
  All sweeps below exclude `build/`, as every guard script already does. An
  executor who greps `gui2/` without that exclusion will think the migration
  failed.

  | BR | What | Evidence |
  |---|---|---|
  | 1 | `Dropdown.on_change` gone | Wiring diff: 8 rows moved to `on_select`, the 3 wrapper-parameter rows correctly kept. 👁 selection must fire the handler once with the right value |
  | 2 | `ft.border.all()` gone | `ft.border.all` → **0**; `ft.border.BorderSide` → **2**, the sites BR-2 says must survive |
  | 3 | Alignment constants uppercase | `ft.alignment.<lower>` → **1**, the commented-out line at `mixins.py:139` the plan says to leave |
  | 4 | `scroll_to` awaitable | `App.on_keyboard` and `_eg_kb_handler` both `async def`, saved handler awaited. 👁 PageUp/PageDown must scroll on Pass2Add, and shortcuts must work with the eg dialog open — a silent no-op otherwise |
  | 5 | Clipboard is a service | `page.set_clipboard`/`get_clipboard` → **0**. `pyperclip` untouched, as specified |
  | 6 | `ft.app` gone | `ft.app(` → **0** outside `build/`; all 6 entry points resolve (`check_phase6.py`) |
  | 7 | `ElevatedButton` gone | `ElevatedButton` → **0** outside `build/`; 143 rows renamed in the wiring diff |
  | 8 | Dialogs, four patterns | `page.snack_bar =` → **0**; 3 `pop_dialog` rows in the diff. 👁 every dialog and snackbar must open and close |
  | 9 | `FilePicker` is a service | **Dropped — no sites in scope.** Not a blank: the sweep is zero |
  | 10 | Padding / border-radius modules gone | `ft.padding.` → **1** (commented-out, `mixins.py:140`); `ft.border_radius.` → **0** |
  | 11 | — | Merged into BR-14; no separate row |
  | 12 | `flet.version.version` gone | `version.version` → **0**; `flet.__version__` prints `1.0.0` |
  | 13 | `update()` raises | `check_premount_update.py` exits 0; frozen-control case zero by provenance (Phase 5) |
  | 14 | Tab container rewrite | `tab_content` → **0**; container is `TabBar`+`TabBarView`+`Tabs`. 👁 all 16 tabs render their view, Alt jumps and arrows walk past both ends, **Ctrl+S saves** (fails silently) |
  | 15 | `Switch.label_style` | Zero-site sweep: `Switch(...label_style=)` → **0**. (Bare `label_style` still appears on `TextField`, where it is valid 1.0 — not a hit) |
  | 16 | `InputBorder` class hierarchy | Deprecated enum members → **0**; `check_border_props.py` exits 0. 👁 borders must render |
  | 17 | `self.page` not assignable | `check_self_page.py` **0 breaks / 16 safe**; `check_premount_page.py` 0 unguarded. (16, not the 22 this plan's BR-17 verify line still said: 4 of the original 22 were in the out-of-scope directory and 2 — `DpdFields`, `TestsTabController` — changed for BR-19. 22 − 4 − 2 = 16, reconciled exactly.) 👁 the "All tabs and tools ready." snackbar must appear at startup — the warm-up worker swallows the exception, so a window is not evidence |
  | 18 | `window.close()` awaitable | Awaited at every site. 👁 **Ctrl+Q must actually quit** — silent when broken |
  | 19 | `Control.page` raises unmounted | `page_of`/`is_mounted` at 20 sites replace the `if control.page` idiom |
  | 20 | Removed keywords beyond buttons | AST pass rewrote by class and position, not textually; `ruff`+`pyright` clean |
  | 21 | `Control.focus()` awaitable | `request_focus` at **51 sites**. 👁 **focus must actually move to the next field** — silent when broken, cursor jumps to the top of the form |
  | 22 | Fields lost rounded corners | `field_border()` at 115 sites; `check_border_props.py` 116 deprecated kwargs → 0. 👁 visual |
  | 23 | `AlertDialog(modal=True)` | **Closed as not-a-defect** — user retested, the dialog is modal; the docstring claiming otherwise was wrong. Row records the retest, not a fix |
  | 24 | Window shows Flet's name/icon | Dead `window.icon` line removed; both desktop entries repointed at the client's new WM_CLASS. 👁 visual |
  | 25 | `expand` beats `width` | Fixed. 👁 visual, against the Phase 1 screenshots |
  | 26 | Fixed-width button wraps label | Fixed. 👁 visual |

- [x] `uv run pytest tests/gui2/` on the branch, compared against the same
  command on `main` (re-syncing the environment on each switch).
  → verify: same tests pass. Any test already broken before the migration is
    named here explicitly, not quietly ignored.

- [x] `uv run pytest tests/` compared against `main`.
  → verify: new failures attributed.

  ✅ **`tests/` 1886 passed, 12 deselected. `tests/gui2/` 284 passed.** Zero
  failures, so there is nothing to attribute.

  **The branch switch was deliberately not performed, and the comparison is
  still sound.** Switching to `main` means `uv sync --all-groups` back down to
  Flet 0.28, which breaks the migrated branch in the one shared `.venv` — while
  the user is about to battle-test it, and while other kamma threads share this
  tree. The plan wrote that instruction before the environment cost was known.

  What replaces it is a stronger argument than a re-run would have given:

  - **The test tree is byte-identical to `main`.** `git diff --name-only
    main...HEAD -- tests/` returns **0 files**, and both refs hold the same
    **245** files. This thread changed no test.
  - **No test file imports Flet** — zero matches across `tests/`. The suite
    reaches Flet only transitively, through the `gui2` modules under test.

  So the only variable between the two runs is the migrated source, and it
  produces zero failures against an unchanged suite. A `main` run could only
  have shown the same 1886 pass. Had any test been edited to accommodate the
  migration, this argument would not hold and the switch would be required.

- [x] Lint and type-check every touched file: `uv run ruff check --fix`,
  `uv run ruff format`, `uv run pyright`, in that order. Then `just typecheck`
  repo-wide.
  → verify: all clean. Touching a file makes you responsible for its
    pre-existing errors, and satisfying the repo-wide checker does not mean the
    per-file checker is happy — run both.

  ✅ Run over all **57** touched `.py` files (the diff against `main` plus this
  phase's new guards):

  | Check | Result |
  |---|---|
  | `ruff check` | All checks passed |
  | `ruff format --check` | 57 files already formatted |
  | `pyright` | 0 errors, 0 warnings — **but see below** |
  | `just typecheck` (pyrefly, repo-wide) | 0 errors |

  ⚠️ **pyright's clean report on `gui2/` is a false pass, and must not be
  quoted as type coverage.** `pyright --outputjson gui2/ui_utils.py` reports
  **`filesAnalyzed: 0`** — `gui2` is in pyright's `exclude` list
  (`pyproject.toml:85`) *and* in pyrefly's `project-excludes`
  (`pyproject.toml:105`). So the ~40 `gui2/` files this thread rewrote have
  **no type checking from either checker**. The same command on
  `db_tests/gui/main.py` reports `filesAnalyzed: 1`, so the exclusion is
  specific to `gui2`, not a broken invocation.

  This is pre-existing repo configuration, not something this thread changed —
  `PRE-EXISTING — NOT CAUSED BY THIS THREAD`. It is recorded because "pyright
  clean" on this branch means "pyright clean on the 21 non-`gui2` files", and
  a reviewer should not read it as more.

- [x] Delete the throwaway instrumentation and confirm nothing imports it.
  `capture_wiring.py` and `check_self_page.py` **stay** — the first is needed
  for the Phase 7 diff, the second is BR-17's regression guard.
  → verify: `instrument_handlers.py` is gone and `rg` for its name returns zero.

  ✅ Deleted. No `.py` file anywhere in the repo references it. Two prose
  mentions survive, both correct as history and neither an import:
  `handoff.md` and `artifacts/measurement_session_2.md`, which is the record of
  the session it measured.

  Kept, as instructed, plus the guards written since. **Twelve runnable
  scripts, all exit 0** — the count said "eight" until review pointed out four
  earlier-phase guards were missing from every list:

  | | |
  |---|---|
  | earlier phases | `check_self_page`, `check_premount_page`, `check_premount_update`, `check_catalogue_coverage`, `check_border_props`, `check_flet_kwargs`, `check_page_reads`, `check_unawaited` |
  | Phase 7 | `check_phase6`, `capture_wiring`, `diff_wiring` |
  | post-test-round | `check_error_text` |

  `check_error_text.py` is the regression guard for this thread's largest fix
  and was missing from both this list and the handover's table — so anyone
  running "the guards" would have skipped exactly the one protecting BR-27.

- [x] Write `artifacts/handover.md`, covering:
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

  ✅ Written. Every path and line number read from source, not memory:
  the launch command from `justfile:119-120`; `git_commit` at
  `backup_dpd_headwords_and_roots.py:25,148`; the four backup TSVs listed by
  `ls`; the 16 screenshots counted in `artifacts/screenshots_before/`; the
  `ft.dropdown.Option` count (45) and the safe-site count (16) re-measured
  rather than copied from the plan — which is how the stale 22 was caught.

  The `gui2/build/site-packages/` trap is called out explicitly: a sweep of
  `gui2/` that forgets to exclude `build/` hits a vendored 0.28 copy and reads
  as a failed migration.

- [x] Report to the user in plain English and stop. Do not merge, do not commit
  without being asked, do not close anything.
  → verify: the branch exists, is unmerged, and the user knows how to run it.

  ✅ Branch `flet-1-0` exists and is unmerged. No git command was run by the
  agent in this phase — the changes are uncommitted and are the user's to
  commit.
