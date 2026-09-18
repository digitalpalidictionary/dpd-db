# Slow handlers — 0.28.3 baseline

Source: `handler_timing.csv`, 213 invocations from one real editing session,
2026-09-17. Captured on Flet 0.28.3 before any migration edit.

Phase 4 re-runs the same instrumentation against 1.0.0 and compares.

## Read this before using the numbers

**Almost everything here is a single sample.** 44 of the 63 measured
handler/event pairs have `n=1`. A median of one is a reading, not a
measurement. Phase 4's gate explicitly says a handler measured once is not
measured, so anything acted on below gets re-measured with a real sample first.

**Coverage is partial — 6 files of the in-scope 35.** The session was mostly
Pass2Add, plus the translations tab and the word finder. Un-exercised:
pass1 add and auto, pass2 auto and pre, pass2x, filter, tests, roots, sandhi,
compound type, bold search, global, and every popup but the word finder.

Consequences for this task's verify line, honestly stated:

| Shortlist item | In the log? |
|---|---|
| Sanskrit entry points | 3 of 4 — `sanskrit_submit`, `sanskrit_focus`, `sanskrit_blur` |
| `family_word_change`, `pattern_change`, `root_key_change` | yes, all three |
| the two TSV re-readers | **no** — not reached this session |
| CST book search | **no** — not reached (the 1.7 s row is the translations search, a different path) |
| the subprocess launches | **no** — not reached |

Four known-slow operations are therefore absent because they were never
triggered, not because the instrumentation missed them. The hook is at the
dispatch boundary and demonstrably catches lazily built views —
`translations_view` and `wordfinder_popup` both appear, and neither exists at
startup.

## Thresholds

Classified by what the user is doing, not by the event's name. A tab change is
not a keystroke, so it is judged as an action, not against the typing budget.

| Class | Budget |
|---|---|
| keystroke — `change` on a text field, `keyboard_event` | 50 ms |
| focus / blur / submit | 150 ms |
| click, tab change, hover | 300 ms |

## Over budget

| Median | Max | n | Budget | Handler | Site |
|---:|---:|---:|---:|---|---|
| 1736.3 | 1736.3 | 1 | 150 | `TranslationsView.search_clicked` | `gui2/translations_view.py:122` |
| 1090.5 | 1090.5 | 1 | 150 | `DpdFields.sanskrit_submit` | `gui2/dpd_fields.py:970` |
| 811.9 | 1623.8 | 2 | 300 | `App._on_tab_activated` | `gui2/main.py:300` |
| 496.0 | 496.0 | 1 | 300 | `Pass2AddView._click_add_to_db` | `gui2/pass2_add_view.py:789` |
| 438.3 | 438.3 | 1 | 150 | `Pass2AddView._click_edit_headword` | `gui2/pass2_add_view.py:448` |

Blocking operation per row, read from the handler bodies:

- **`search_clicked`** — full-text search across the translations corpus. The
  slowest thing measured, and it runs on the UI thread.
- **`sanskrit_submit`** — network or corpus lookup. The spec's shortlist already
  named the Sanskrit entry points; this confirms one of them.
- **`_on_tab_activated`** — the lazy build of a whole view on first selection.
  The two samples are first-build (1623.8 ms) and re-selection (0.0 ms), which
  is the lazy-build design working, not a regression. It is unavoidable work; it
  needs a progress indicator, not a lower number. **Note both samples fired
  twice**, once as `click` and once as `change` — the duplicate dispatch the
  plan's BR-14 task expects to confirm before editing. This log is that
  confirmation.
- **`_click_add_to_db`** — the database write. Acceptable for an explicit save
  button, but it is the one action where a freeze is least tolerable.
- **`_click_edit_headword`** — loads a headword into the form.

## Tail offenders — fast median, slow tail

Both are keystroke-path handlers with real sample counts, and both breach the
50 ms budget at the tail. These matter more than several of the single-sample
rows above, because they happen while the user is typing.

| Median | Max | n | Handler | Site |
|---:|---:|---:|---|---|
| 35.9 | 68.8 | 11 | `DpdCommentaryField.clean_text` | `gui2/dpd_fields_commentary.py:355` |
| 0.0 | 66.7 | 72 | `App.on_keyboard` | `gui2/main.py:217` |

`on_keyboard` is free 70 times out of 72 — the tail is the two presses that
trigger a tab jump, so it is `_on_tab_activated`'s cost surfacing through the
keyboard path rather than a second problem.

## Long work, correctly backgrounded already

Not defects. Listed because Phase 4 must not "fix" them, and because they are
the two places the window is already relying on a worker thread.

| Duration | Worker | Site |
|---:|---|---|
| 15531.5 ms | `App._initialize_db_in_background` | `gui2/main.py:318` |
| 4230.6 ms | `App._warmup_in_background` | `gui2/main.py:328` |

The 15.5 s database initialisation is the single longest operation in the app.
It already runs off the UI thread. What it lacks is a moving progress
indicator, which is Phase 4's responsiveness gate rather than an offload job.

## Everything else

58 handler/event pairs came in under budget, most of them at or near 0 ms.
The 34–40 ms cluster across the field system is uniform enough to look like
dispatch overhead rather than per-handler work.

## What this changes in the plan

Nothing in Phase 3. Phase 4's conversion list starts as: the translations
search, the Sanskrit entry points, the headword load, the database write, and
progress indication for the lazy tab build and the startup database
initialisation — each re-measured with a real sample count before conversion.

The four un-exercised shortlist items (TSV re-readers, CST book search,
subprocess launches) still need measuring. Either a second session on the
un-touched tabs before the upgrade, or they carry into Phase 4 measured on 1.0
only, with no before-picture to compare against.
