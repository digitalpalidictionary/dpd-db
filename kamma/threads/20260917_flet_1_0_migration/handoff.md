# Handoff — 2026-09-17, Phase 5 complete, awaiting the user's test

## Where to start

**Phase 6 — the other Flet consumers.** First task: launch the 7 data-integrity
GUI helpers. Phases 0–5 are done; Phase 6 is partly done already (the renames
and typing were pulled forward into Phase 3), so what remains there is BR-9 and
the launch checks.

Phase 5's code changes are **uncommitted and not yet user-tested**. Ask for the
test before moving on.

## State

| Phase | State |
|---|---|
| 0–4 | done, committed through `d6891c48` |
| 5 | **done in code, awaiting the user's test** |
| 6 | partly done — BR-9 and the launch checks remain |
| 7 | not started |

Branch `flet-1-0`. Four modified source files, one new guard script, all this
thread's; `artifacts/instrument_handlers.py` stays untracked on purpose (AD#4).

## What Phase 5 landed

Two sweeps came back empty and one found real work.

**Pre-mount refreshes: zero.** A new guard, `artifacts/check_premount_update.py`,
walks the call graph out of every control subclass's constructor looking for
`update()`. Its first run printed six hits and every one was a false positive —
four were the `page or page_of(self)` alias from BR-17's own fix, two were
inside `on_select` lambdas. The scanner was tightened to recognise both, and its
sensitivity re-proved against a synthetic case. No source line changed.

**The frozen-control case: zero, by provenance.** `_frozen` is set in exactly
two places in the wheel and both are inside the declarative components API. A
grep for every entry point into that API across `gui2/` and `db_tests/gui/`
returns nothing, so no control here can ever acquire the marker. That is a
better answer than a clean walk of the catalogue, which is what the plan
originally asked for.

**Six progress handlers converted.** Each set a status message and then blocked
the event loop, so the message it was meant to show only appeared once the work
was already over: the database backup, the inflections update, the speech-marks
regeneration, the per-word AI update, the standalone AI search window, and the
three-step start of a test run. All are now `async def` with the slow half on
`asyncio.to_thread`.

## Three things worth knowing before Phase 6

1. **1.0 supports generator handlers natively.** `BaseControl._trigger_event`
   has a branch for them that flushes the queued patch and yields to the loop on
   every `yield`. The plan's "convert to yielding generators" was therefore
   sound, but `async def` + `to_thread` was used instead — it satisfies the same
   requirement and also keeps the window alive, and the user has already
   confirmed that pattern from Phase 4.

2. **Awaiting an offload is itself the flush.** Where the message and the
   `await to_thread(...)` sit next to each other there is no need for a separate
   `sleep(0)`; the suspension hands the loop the turn that paints the message.
   The explicit sleep is only needed where the two are separated — the test
   run's integrity check is the one place in Phase 5 that needs it, because that
   step writes to the view and so cannot be offloaded at all.

3. **The `dialog.open = False` sites are not a missed conversion.** Fifteen of
   them survive, and they looked like BR-8 leftovers. `pop_dialog()` is
   literally the same two statements, so they are equivalent. Logged as
   `NOTICED — NOT TOUCHING` rather than swept.

Still carried forward from Phase 4, still not blocking: `_click_add_to_db`
blocks the loop on a synchronous spell check and an HTTP call, and pyright
reports a false pass on `gui2/` because it analyses zero files there.

## What the user needs to test

The six converted actions, watching for the progress message to appear *before*
the work rather than after: Global tab's backup-and-quit and update-inflections,
Pass2Add's update-sandhi and update-with-AI, the Ask AI window, and the Tests
tab's Run button. The window should also stay responsive throughout.

## Verification state

`uv run pytest tests/` 1886 passed / 12 deselected · `tests/gui2/` 284 passed ·
`just typecheck` 0 errors · `ruff check` and `ruff format` clean on all four
touched files plus the new guard · all four modules import · all four guard
scripts exit 0.
