# Handoff — 2026-09-17, Phase 4 in progress

## Where to start

**Phase 4, second measured session.** The conversion task cannot be scoped
until the pass views have been measured on 1.0 — see the coverage gap below.

## State of Phase 4

| Task | State |
|---|---|
| Port the instrumentation and re-run | measured once; **coverage insufficient**, needs a second session |
| Convert the slow handlers | blocked on the above |
| Audit the pre-existing concurrency | **done** — nothing to fix, evidence in `plan.md` |
| Audit the non-database blocking | not started |
| Phase verification | not started |

## What this session did

**Ported the instrumentation.** 0.28 had three dispatch routes; 1.0 funnels all
four handler shapes through one method. The trap: that method also flushes the
UI patch afterwards, which would have inflated every row against the 0.28
baseline, worst for the handlers touching the most controls. Framework time is
measured separately and subtracted. Verified headlessly against all four shapes
(20.3 / 30.6 / 20.6 / 30.8 ms against injected 20/30/20/30).

**First 1.0 session captured: 367 invocations, 6 files, 18:12–18:18.** Nothing
on the UI thread is meaningfully over budget; the worst is one compound-type
submit at 192 ms against a 150 ms budget, `n=1`. The keyboard handler BR-4 made
async ran 188 times at a 0.5 ms median. Both background operations came in
faster than 0.28 (11.7 s against 15.5 s; 3.35 s against 4.2 s).

**The concurrency audit is closed, and the risk it raised is not real.** The one
raw thread touches no control at all. The cross-thread delivery concern —
worker-thread refreshes landing on the loop's queue through a call that is not
thread-safe — was disproved by the log rather than by reading: Flet wraps every
snackbar's dismissal, so a snackbar that renders leaves its own row, and both
startup snackbars dismissed ~2.55 s after their worker finished against a
2000 ms duration. They painted promptly from the worker thread. The user simply
missed a 2-second message during an 11-second load. That also closes BR-17's
outstanding evidence gate, since the warm-up snackbar only fires when all 16
views built.

**Two defects fixed from the user's screenshots**, both recorded as spec items:

- **BR-26** — 1.0 leaves less room for a button's label at the same width, so
  the Filter tab's preset buttons wrapped mid-word. Measured first: the 0.28
  pills were exactly 80/100/80 px with their labels on one line, and 1.0
  honours the same numbers, so the width was never the variable. Those three
  now size to their labels. An AST sweep bounds the rest: 11 narrow buttons
  exist, the other 8 have short enough labels.
- **BR-24, third scope change** — the title bar showed `flet`. Not setting the
  title leaves it `None`, which the client fills with its own name; the empty
  string is what means "show nothing". Now set explicitly.

## Coverage gap — read before scoping the conversions

The measured session was the Filter tab and the Compound Type tab. The pass
views have **one row between them**, and the four shortlist items the 0.28 run
also missed — the two TSV re-readers, the CST book search, the subprocess
launches — are still unexercised. A conversion list built on this would be a
guess wearing a measurement's clothes.

The db edits the user reported were **not** in this window: the latest headword
writes are from 12:44, and nothing was created or updated after 17:00. Their
examples were checked anyway and are clean.

## What the user needs to do

1. **A second instrumented session, on the pass views** (Pass1Add, Pass2Add,
   Pass2Pre, Pass2x) and any tab with a TSV re-read, a book search or an
   external-application launch:

       uv run kamma/threads/20260917_flet_1_0_migration/artifacts/instrument_handlers.py

   It appends to `artifacts/handler_timing_1_0_0.csv`.

2. **Confirm the two fixes** after a relaunch: the Filter tab's `Save`,
   `Rename` and `Delete` on one line each, and no name in the title bar.

Still owed from Phase 3, unchanged: BR-25's dropdown widths, the taskbar name
and icon, and a field taking focus.

## Tree state

Green: full suite 1886 passed / 12 deselected, `tests/gui2/` 284 passed,
`just typecheck` 0 errors, `ruff` and `pyright` clean on both touched files.

Two production files modified and ready to commit — `gui2/filter_tab_view.py`
and `gui2/main.py`, both migration fixes, no improvement mixed in. Plus this
thread's `spec.md`, `plan.md` and `handoff.md`.
`artifacts/instrument_handlers.py` stays untracked on purpose (AD#4); the new
`artifacts/handler_timing_1_0_0.csv` is measurement data.
