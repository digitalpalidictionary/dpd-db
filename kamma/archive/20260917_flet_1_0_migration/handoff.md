# Handoff — 2026-09-18, all phases done and user-confirmed, ready for review

## Where to start

**Nothing to implement. Run `/kamma:3-review` in a fresh session.**

Every task in `plan.md` is `[x]`. The user ran the full test round (13 of 15
passed), the three resulting BR items were fixed, and all four retests are
confirmed. Two follow-ups stay open by the user's own decision — eg-dialog
modality and the residual focus jumps — and are recorded in `spec.md` →
*Out of scope*, not as thread debt.

## What the test round changed

Three BR items, all fixed and retested:

- **BR-27** — the significant one. 1.0 renamed `TextField.error_text` to
  `error` but left `Dropdown.error_text` alone, and assigning the dead name is
  silently accepted. **~60 validation messages across the editor had stopped
  appearing**, and the reported symptom was only one missing red border. The
  test-failure code's own `hasattr(field, "error_text")` guard went False on
  every text field, so it skipped highlighting rather than failing. Fixed with a
  forwarding property (keeps all 60 call sites) plus the border derived in
  `before_update()`. Guard: `check_error_text.py`, sensitivity proved by
  reintroducing the bug.
- **BR-28** — dropdowns held a literal `width=700` where the text fields
  expand, leaving them ~65px wider. Same `expand=True` now on both.
- **BR-29** — the six `db_tests/gui/` tools each run a whole review session
  inside the click handler behind `while True: sleep(0.1)`. 0.28 ran sync
  handlers on a worker thread; 1.0 runs them on the event loop, so the window
  froze after one frame. Fixed in one place with `page.run_thread`; the six
  tools are untouched. Teardown also moved into a `finally` — it previously ran
  only on success, so a raising tool left the guard flag set and the tool
  silently stopped accepting clicks.

Read `artifacts/handover.md` first — it is the user-facing document and holds
the launch commands, the branch-switch procedure, and the watch-list.

## State

| Phase | State |
|---|---|
| 0–5 | done, committed through `ba4c952d` |
| 6 | **done in code** — all 10 files clean; launching each tool needs a human |
| 7 | **done bar the running-app checks** |

Branch `flet-1-0`, uncommitted. This session touched thread files and artifacts
only — **no source file was changed in Phases 6 or 7.**

## What changed this session

**The updater was removed from the thread entirely**, per the user: a dead side
project that never belonged here. Its submodule was already clean at `v0.0.2`
on 0.28.3 and stayed untouched. Stripped from `spec.md` (revision 10),
`plan.md` (revision 13), `behaviour_catalogue.md`, and the two scanner scripts'
comments. BR-9 existed only for it and is now a zero-site sweep.

Counts that moved with it, all re-derived rather than edited by hand: BR-6 is
6 entry points not 7; BR-8 is 14 closes not 15; the in-scope binding total is
449 not 463.

**Phase 6** — new guard `artifacts/check_phase6.py` covers all 10 files
(`db_tests/gui/`, `gui2/utilities/`, `gui2/test_app.py`) in one pass: 16
removed-API spellings, imports, and entry points resolving. Exits 0. Its
sensitivity was proved, not assumed — all 16 patterns fired on a known-bad
line, and the 9 correct 1.0 spellings produced no false positives.

**Phase 7** — new `artifacts/diff_wiring.py` and `artifacts/wiring_diff.md`:
**zero unexplained differences**, 449 → 448 bindings, every one classified.
`artifacts/handover.md` written. The throwaway instrumentation is deleted.

## Three things the next session should know

1. **`gui2/build/site-packages/` is a vendored Flet 0.28 copy.** A `grep` over
   `gui2/` for removed API that forgets to exclude `build/` returns 69 hits for
   `ft.app(` and 37 for `ElevatedButton`, and looks exactly like a failed
   migration. Every guard already excludes it.

2. **`pyright` reporting clean on `gui2/` is a false pass.**
   `pyright --outputjson gui2/ui_utils.py` says `filesAnalyzed: 0` — `gui2` is
   excluded from pyright (`pyproject.toml:85`) *and* pyrefly
   (`pyproject.toml:105`). The ~40 rewritten `gui2/` files have no type
   checking at all. Pre-existing config, not this thread's doing, but do not
   quote "pyright clean" as coverage.

3. **Two stale numbers were corrected from measurement.** The safe `self.page`
   count is **16**, not the 22 the plan asserted (22 − 4 out-of-scope − 2
   changed for BR-19). And the dropdown split is 7 direct sites plus the
   wrapper = **8**, not the 9 Phase 7's prose said. Both are now measured
   values in `spec.md` and `plan.md`.

The improvements audit also found three shared helpers (`page_of`,
`is_mounted`, `request_focus`, 71 call sites) missing from
`artifacts/improvements.md`. They are BR fixes rather than improvements, so
their absence from the taken-improvements table is correct — but the log now
says so explicitly, in a new section, so a reviewer does not have to guess.

## Testing state

**Done.** The user walked all 15 checks plus the four retests; nothing is
outstanding for them. `artifacts/handover.md` keeps the watch-list for ongoing
battle-testing.

## Verification state

`uv run pytest tests/` **1886 passed, 12 deselected** · `tests/gui2/`
**284 passed** · `just typecheck` **0 errors** · `ruff check` and
`ruff format --check` clean on all **57** touched files · wiring diff **zero
unexplained** · all **8** guard scripts exit 0.
