# Handoff — 2026-09-17, end of the Phase 3 fix session

## Where to start

**Phase 4 — Threading model**, first task: port the instrumentation to the 1.0
dispatch boundary and re-run it. Everything before that is done or waiting on
the user.

## What this session did

Closed the four issues the user's battle-testing left open. Committed as
`7c01efb8` on `flet-1-0`, 35 files.

- **BR-22 (borders).** `field_border()` in `gui2/ui_utils.py`; 116 deprecated
  kwargs across 84 constructions converted; 28 borderless fields given an
  explicit rounded border; BR-16's red signals moved to `.border`;
  `cell_border()` in `filter_component.py` keeps the grid cell's own shape.
  User confirms the corners are round again.
- **BR-23 (dialog modality).** **Not a defect.** Retested: the eg dialog does
  not dismiss on an outside click. The wheel's `modal` docstring is wrong;
  Flet's Dart at tag `v1.0.0` passes `barrierDismissible: !modal`. No code
  changed, and flipping all 18 `modal=True` sites would have been a mistake.
- **BR-24 (window identity).** `window.icon` is Windows-only and wants `.ico`,
  so the earlier attempt was inert — line removed. The taskbar name and icon
  come from the desktop entry: 1.0's client reports `com.appveyor.flet` where
  0.28 reported `flet`, so `StartupWMClass` was repointed in both
  `gui2/linux/dpd-gui2.desktop` and the installed copy. The window title is
  now unset, at the user's request.
- **BR-25 (new).** `DpdDropdown` passed `expand=True` and `width=700` together;
  1.0 lets `expand` win where 0.28 let `width` win, so the pass views'
  dropdowns went 665px → 1251px. `expand` dropped from the dropdown only.

## The method worth repeating

BR-25 was found by *measuring* the user's screenshot against
`artifacts/screenshots_before/07_pass2add.png`, not by reading code. Field
heights, row pitch, text insets and outline brightness all came out identical
across versions, which ruled out the border pass and left the one real
difference visible. The user had already sat through two wrong guesses at
BR-22; measuring first is what ended it.

Likewise BR-23: the installed wheel's docstring contradicted the shipped Dart,
and only fetching Flet's source at the exact release tag settled it. AD#2 says
the wheel is the authority — that has to mean the shipped client, not the
Python docstring.

## Open, and needing the user rather than code

- **Phase 3 verification:** walk the whole behaviour catalogue in the running
  app. Still `[ ]`.
- **Confirm BR-25 visually:** the dropdowns should stop well short of the text
  fields' right edge, as in the before shots.
- **Confirm the taskbar** shows the DPD name and logo after a fresh launch.
- **Watch a field take focus.** BR-22 gave some fields an explicit border
  `side`. The wheel says that styles the enabled state only and leaves the
  other states theme-resolved — the same division 0.28 had — so parity is
  expected but unobserved. Cheapest to check now rather than meet as a mystery.

## Two review findings that did not hold

Recorded so nobody re-raises them. A reviewer reported `uv run ruff check gui2`
returning 167 errors from the vendored `gui2/build/site-packages/`; on this
tree it returns "All checks passed!", because `gui2/build/` is gitignored
(`.gitignore:93`) and ruff respects gitignore by default. And a reviewer asked
for a sweep for un-awaited coroutines; `artifacts/check_unawaited.py` already
is that sweep — it reads the coroutine list off the installed wheel and
currently reports 0.

## Tree state

Clean on `flet-1-0` apart from
`artifacts/instrument_handlers.py`, which is untracked on purpose — throwaway
instrumentation, never committed (AD#4).

Green at the commit: `uv run pytest tests/` 1886 passed / 12 deselected;
`tests/gui2/` 284 passed; `just typecheck` 0 errors; `ruff` and `pyright` clean
on every touched file.
