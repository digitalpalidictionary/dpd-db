# Handover — Flet 0.28.3 → 1.0.0

> ⚠️ **The shared working tree is parked on branch `flet-1-0`.**
> Any other kamma thread that commits here lands on the migration branch, not
> `main`. Check `git branch --show-current` before staging anything.

## Launching the migrated editor

```
just gui
```

which runs `uv run python gui2/main.py` (justfile:119-120). Nothing else
changed about how it starts.

## Switching branches

One `.venv` holds one Flet, so **a branch switch is not complete until the
environment is re-synced**. Both directions, literally:

```
# to the migration branch
git status --porcelain      # other threads share this tree — look before you switch
git switch flet-1-0
uv sync --all-groups

# back to main
git status --porcelain
git switch main
uv sync --all-groups
```

Skipping the sync leaves 1.0 code running against 0.28, or the reverse. Most of
the failures that produces are silent.

`uv sync` alone is not enough — it strips the dev and lint groups.

## Where the database backup is

`db/backup_tsv/dpd_headwords_part_001..003.tsv` plus
`dpd_roots_part_001.tsv`, the repo's own TSV backup. These are git-tracked, so
the restore point is a commit, not a loose file.

No binary copy of `dpd.db` was taken. The branch changes no schema and no
data-writing code.

⚠️ **Do not run `just backup` to refresh it from this branch.**
`backup_dpd_headwords_and_roots` calls `git_commit` unconditionally as its last
step (`db/backup_tsv/backup_dpd_headwords_and_roots.py:25,148`). It commits every
`dpd_headwords_part_*.tsv` and `dpd_roots_part_*.tsv` as `pali update`, **on
whatever branch is checked out** — so from here it would put a data commit on
the migration branch. The recipe reads as read-only and is not.

This thread made that commit path safer in a shared tree — it is now
path-limited, so it can no longer sweep up another session's staged work, and it
leaves nothing staged when it fails. It still commits, and still on the current
branch, so the warning above stands.

## What to watch for while battle-testing

**Any moment the window stops responding.** That is the whole point of Phase 4
and Phase 5, and it is the one thing no static check can see.

Then the **silent failures** — each of these fails with no error message, no log
line, and a perfectly normal-looking screen. "Nothing crashed" is not evidence
for any of them:

| Watch | Broken looks like |
|---|---|
| Dropdown handlers (BR-1) | selecting a value does nothing downstream — no autofill, no gloss |
| PageUp / PageDown on **Pass2Add** (BR-4) | the middle section simply does not scroll. Only this tab (Alt+E) responds; testing elsewhere proves nothing. Numpad 9/3 are the same keys with Num Lock off |
| Keyboard shortcuts **while the eg dialog is open** (BR-4) | global keys stop working until the dialog closes |
| **Ctrl+S** on Tests or Roots (BR-14) | the save quietly does not happen |
| **Ctrl+Q** (BR-18) | the app does not quit |
| **Focus moving to the next field** (BR-21) | the cursor jumps back to the top of the form after each edit |
| The **"All tabs and tools ready."** snackbar at startup (BR-17) | it never appears. The warm-up worker swallows its own exception, so the window opening and the first tab rendering prove nothing |

And the **visual** items, best judged against
`artifacts/screenshots_before/` (16 shots, `00_global.png` … `15_ct.png`, in tab
order): rounded field corners (BR-22), field widths (BR-25), button labels not
wrapping mid-word (BR-26), window name and icon (BR-24).

## Known-different, deliberately

- **A tab activation now fires its handler once, not twice.** 0.28 bound both
  `on_click` and `on_change` on the tab container. The dedup guard absorbed the
  duplicate, so nothing user-visible changes.
- **`pop_dialog()` closes the topmost dialog** rather than a named one. Every
  call site closes the dialog it just opened with nothing stacked above it, so
  behaviour is preserved — but a future *nested* dialog would behave differently.
- **`FieldConfig.on_change` keeps its name** across all 50 field definitions,
  and the `DpdDropdown` wrapper forwards it to `on_select`. The name is now
  slightly misleading; renaming it is a cosmetic rename, out of scope (AD#8).

## Not migrated, on purpose

- `ft.dropdown.Option` (45 sites), the two `ft.border.BorderSide` calls, and the
  16 safe `self.page` assignments on plain (non-control) classes — those classes
  are not controls, so `page` stays an ordinary attribute. Renaming for taste is
  not structural improvement (AD#8).
- `pyperclip` in `tests_tab_controller.py` is not a Flet API and was left alone.
- `gui2/build/site-packages/` holds a **vendored copy of Flet 0.28** as a build
  artifact. It is untouched and excluded from every sweep. A `grep` for removed
  API across `gui2/` that forgets to exclude `build/` returns dozens of hits and
  looks like a failed migration.

## If something misbehaves: migration, or refactor?

Read **`artifacts/improvements.md`** first. It maps every structural change to
the BR item that opened its file, with the evidence that behaviour is unchanged,
so the first question has a written answer and the rollback is "revert these
named hunks" rather than an unpicking exercise.

Two genuine improvements were taken — `field_border()` (117 call sites) and
`cell_border()`. Three shared helpers (`page_of`, `is_mounted`, `request_focus`,
71 call sites between them) are **BR fixes, not improvements**, and reverting one
reinstates a broken 1.0 idiom rather than restoring 0.28 behaviour. That section
of the log says so explicitly.

## Verification state at handover

| Check | Result |
|---|---|
| `uv run pytest tests/` | 1886 passed, 12 deselected |
| `uv run pytest tests/gui2/` | 284 passed |
| `just typecheck` (pyrefly, repo-wide) | 0 errors |
| `ruff check` / `ruff format --check`, 57 touched files | clean |
| `pyright`, 57 touched files | 0 errors — **but `gui2/` is excluded, see below** |
| Wiring diff, 449 → 448 bindings | zero unexplained differences |
| All 10 guard scripts + `capture_wiring` / `diff_wiring` | exit 0 |

⚠️ **`gui2/` has no type checking from either checker.** It is in pyright's
`exclude` (`pyproject.toml:85`) and pyrefly's `project-excludes`
(`pyproject.toml:105`); `pyright --outputjson gui2/ui_utils.py` reports
`filesAnalyzed: 0`. Pre-existing repo configuration, not this thread's doing —
but it means "pyright clean" covers the 21 non-`gui2` files and no more.

**What none of this proves:** that the app behaves correctly. Every remaining
risk is silent or visual, which is what the table above is for.

## Open visual check — the one worth doing first

**Pass1Add's dropdowns** (`pos`, `neg`, `verb`, `trans`, `plus_case`) against
`artifacts/screenshots_before/03_pass1add.png`.

BR-28 gave dropdowns the same `expand` as the text fields so their right edges
line up. That is confirmed on Pass2Add. But Pass1Add has a different row shape —
no button, no add-field — so the field slot there expands to roughly the full
row. The text fields already did that in 0.28 and still do; the dropdowns did
not (BR-25 measured them at 665px). So on Pass1Add the dropdowns are now aligned
with the text fields but **wider than their 0.28 baseline**.

The retest cannot tell the two apart — "edges aligned" is true either way. If
the full-row width on Pass1Add is unwanted, say so and it becomes per-row-shape
handling rather than one global flag.

## Also worth watching

- **The `db_tests/gui/` tools under rapid clicking.** They now update the window
  from a worker thread while the event loop may do the same, and 1.0's patch
  generation has no lock on that path. This is the model 0.28 used and the one
  Flet's own `run_thread` API implies, so it is convention rather than proof.
  A dropped repaint under contention is the thing to look for.

## Still owed

The test round closed nearly everything. What is genuinely still unobserved:

- **Three of BR-16's four border signals** — a 300-character example, invalid
  filter input, and the book dropdown's grey border. The fourth (a failing
  field going red) is confirmed, and was broken until BR-27.
- **BR-22's focused border.** Nobody has watched a field take focus. One click
  into a dropdown and into a coloured text field settles it.
- **The per-field dropdown behaviours** in catalogue §1.3 beyond the two the
  round exercised.

Everything else is confirmed: all 15 numbered checks, the four retests after
BR-27 to BR-29, the `db_tests/gui/` helpers (antonyms sync run end to end), and
both `gui2/utilities/` scripts.

Two follow-ups are open by the user's own decision and are not thread debt:
eg-dialog modality, and the residual focus jumps.
