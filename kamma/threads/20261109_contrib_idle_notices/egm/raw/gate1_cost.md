# Goldfish review — cost, quota, resource economics

Measured baseline: warm 943.3 MB, 1,045.7 MB after one book (peak 1,113.4). The hypothesis's 1.2–1.5 GB is stale but the plan's economics don't depend on it. The plan is mostly sound; the failures are in the wake storm, the cold-start cost, and the fact that nothing caps a process.

## Blockers

**1. The idle exit does not reclaim what the plan assumes, and the wake rebuild costs the same as it saved.**
`gui2/main.py:711-760`. Exiting the process does free everything (unlike dropping objects in-process — the hypothesis is right about that). But the "empty ~87 MB" state is only reachable while nobody connects. Every reconnect runs `App(page)` (`gui2/main.py:841`), then `build_ui` → `_initialize_db_in_background` → `_warmup_in_background` (`gui2/main.py:657-704`), which rebuilds corpus + inflection hashes + detector unconditionally, no matter which tab the wake page lands on. Cost per wake: ~11 s of pure CPU on 2 vCPU (the code's own figure, `gui2/main.py:609`) plus 943 MB, before the user does anything. A contributor who opens the editor, reads, closes it, and opens it once more an hour later pays the full 1 MB→943 MB ramp twice. The plan saves memory only for people who stay away; it saves *nothing* for the common read-a-word-and-leave pattern, and it adds a 60-second wall to each of them. Fix: make the contributor warm-up demand-driven (build the corpus only when a save/lookup actually needs it, not on `build_ui`), and measure a real wake→ready latency before promising "about a minute" in the wording.

**2. Simultaneous wakes on 2 vCPU.**
`gui2/main.py:657-704`, `scripts/server_contrib/dpd-gui@.service`. If several contributors return at the same hour (the plan's own premise: a global user base, so overlapping wakes are the normal case, not the edge case), N processes each run an 11 s CPU-bound warm-up. Two vCPUs meant 2 wake-ups serialize; 5 wake-ups is ~30 s of queueing stacked on top, and every instance in the middle of it looks hung. There is no admission control, no niceness, and no shared cache. Fix: the plan needs a wake queue or a per-instance `CPUWeight`/`Nice` so a waking instance cannot starve a working one; otherwise "it takes about a minute" becomes "it takes as long as the neighbours".

## Major

**3. The nightly window's `start` is the same storm, with no warning possible.**
`scripts/server_contrib/maintenance_window.py:453-455` — `_systemctl("start", ...)` starts every instance in a loop inside `finally`, after up to 55 minutes of rebuild. All N processes then run the 943 MB ramp and an 11 s warm-up at once, on the same 2 vCPU that just spent an hour building. Peak RSS is N×~1.1 GB *simultaneously*, not staggered — exactly the shape that reaches swap. Peak here is the plan's worst untested number. Recovery wakes (item 1) can also pile onto this window. Fix: stagger the `start` calls (a few seconds apart is not enough — the ramp is ~20 s, so spacing must exceed that, or the units need `CPUWeight=`).

**4. Nothing in the unit bounds a process.**
`scripts/server_contrib/dpd-gui@.service:10-21`. No `MemoryMax`, despite the archived results (`20261102_contrib_mem_measure/artifacts/results.md`, correction 2) explicitly noting "the cap of 2 GB per instance (`MemoryMax`)" — a cap that does not exist in this unit or in runbook Step 6a. The archived savings thread also records 2,059.4 MB observed with two extra browser sessions in one process (`20261102_contrib_mem_savings/artifacts/results.md`, caveats) — 2× the budgeted figure, and `StartLimitBurst=5`/`Restart=on-failure` means an OOM kill can take the unit down for the night. The plan removes the one thing currently limiting per-process growth (the nightly restart) and replaces it with a timer that may never fire if the idle detection is broken. Add `MemoryMax=2G` before shipping, and check `MemoryMax` behaviour against the on-failure restart policy.

**5. Peak during the rebuild window is unchanged and was never measured here.**
`maintenance_window.py:207-215` — `_capture_rollback` `shutil.copy2`s the whole 883 MB db to `dpd.db.prev` on disk (page cache), so the window adds ~883 MB of dirty pages plus the rebuild's own peak on a machine whose instances "start every night after the window". The plan says instances start after the window; it does not say the box has any headroom then. Fix: no fix required, but the plan's claim that it "reclaims resources for active people" should not be validated at the same time the box is doing its heaviest work.

**6. `page.session`-based idle tracking has no measurement behind it.**
`gui2/main.py:152` sets `page.on_keyboard_event`, and item 3 of the hypothesis proposes counting "last user action" from events. Any activity the plan does not hook (a tab click, a field edit) will read as idle, and the plan's own "still there?" countdown fires under someone who is mid-form. `gui2/main.py:764-770` already documents that a half-filled form is lost on exit. Fix: track activity at the Flet event-dispatch layer, and require the countdown to be visibly acknowledged before exit.

## Nit

**7.** `gui2/ui_utils.py:137` snackbars are the existing status channel — fine for the "asleep" message, but a 30-minute warning delivered via a 2–5 s `duration` snackbar is unreliable (one missed paint and it's gone). A `ft.Banner` in `_web_header` (`gui2/main.py:182-195`) survives and answers the owner's question 4.