## Thread
- **ID:** 20260918_gui2_startup_latency
- **Objective:** Cut gui2 startup latency by making the sutta text index lazy (gui2/books.py) and serialising the warm-up after the database load (gui2/main.py).

## Files Changed
- `gui2/books.py` — `segment_dict`/`word_dict` converted from eager `__init__` mutators to `functools.cached_property`; construction stores identity, paths, eager file lists, `allowable_chars` only.
- `gui2/main.py` — warm-up chained from `_initialize_db_in_background`'s `finally` with a lock-guarded start-once flag; `build_ui` starts only the db worker; both db-init flags' check-and-set under `_build_lock`.
- `tests/gui2/test_books.py` — new: laziness, build-on-first-use, build-once, and None-path sources (4 tests).
- `kamma/threads/<id>/artifacts/*` — measurement harnesses and logs (thread record).

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `gui2/main.py` | `_warmup_started` check-and-set unlockable from two near-simultaneous tab clicks (coderabbit) | duplicate warm-up worker possible | fixed: `_build_lock` covers both flags' check-and-set |
| 2 | major (evidentiary) | plan.md lint tasks | recorded gui2 pyright runs were no-ops — `gui2/**` excluded from pyright and pyrefly | verification claimed clean on zero analysed files | fixed: re-ran with `--project /dev/null` bypass; real results recorded (books.py + test file 0 errors; main.py carries 13 pre-existing errors, all on untouched #212-debt lines — NOTICED, NOT TOUCHING) |
| 3 | minor | `gui2/main.py:358` | `_db_init_started = False` reset in except branch unlocked, inconsistent with new lock discipline | retry-reset could race a concurrent tab click | fixed: reset moved inside `_build_lock` |
| 4 | minor | `tests/gui2/test_books.py` | no test for the four `None`-path sources | laziness contract untested for them | fixed: `test_none_path_source_stays_lazy_and_empty` added |
| 5 | minor | plan.md Phase 3 | "strictly after / never interleaved" stronger than the code guarantees (warm-up thread starts inside `finally`, before the harness stamp) | recorded claim vs code nuance | fixed: wording softened |
| 6 | nit | `tests/gui2/test_books.py` | vacuous re-assertion; `segment_dict`-first chained build untested | harmless | skipped, documented here |

Independent grep re-verification of the spec's load-bearing claims: external consumers of `SuttaCentralSource` are exactly `sc_book`/`cst_books`/`word_dict` (+ dict-key iteration); nothing in view construction or the warm-up touches `.word_dict`/`.segment_dict`. No dead code introduced; `make_segment_dict`/`process_words` fully removed.

## Fixes Applied
- Findings 1–5 fixed during review (see plan.md Phase 3 lint + task 5 records). Finding 6 skipped as nit.

## Test Evidence
- `uv run pytest tests/gui2/test_books.py -q` (scope: 4 new laziness tests) → 4 passed
- `uv run pytest tests/gui2/ -q` (scope: all gui2 tests incl. pass2pre components/file manager) → 297 passed
- `uv run pytest tests/ -q` (scope: whole repo, slow deselected) → 1899 passed
- `just typecheck` (scope: repo-wide pyrefly, gui2 excluded by design) → 0 errors
- `uv run pyright --project /dev/null gui2/books.py tests/gui2/test_books.py` (scope: real analysis bypassing excludes) → 0 errors
- `uv run pyright --project /dev/null gui2/main.py` → 13 errors, all pre-existing on untouched lines (recorded, not fixed)
- Headless measurement (scope: 3 full startup runs via xvfb) → medians 1.20 s first paint / 8.11 s db loaded / 11.12 s tabs warm
- User live verification (scope: real `just gui` sessions): tab click-through, failed-load path ×2 (incl. warm-up-spam regression found & fixed), pass2pre index payback 0.5 s probe

## Not Verified
- pass1auto's first-selection path live (pass1auto not testable this session; same `.word_dict` code path as pass2pre, unit-covered)
- importtime/probe numbers accepted from committed harness outputs, not re-derived by the reviewer
- gui2/main.py's 13 pre-existing pyright errors (migration debt, deliberately out of scope)

## Verdict
PASSED
- Review date: 2026-09-19
- Reviewer: independent reviewer subagent (zero-memory) + coderabbit CLI; findings triaged and fixed by session agent
