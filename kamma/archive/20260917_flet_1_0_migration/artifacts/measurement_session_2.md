# Measurement session 2 — what to exercise, and why

For Phase 4 of the Flet 1.0 migration. Session 1 (2026-09-17 18:12–18:18, 367
invocations) covered the Filter and Compound Type tabs. Everything below is
what it did **not** reach, and the conversion task cannot be scoped without it.

## Launch

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/instrument_handlers.py

It is the ordinary editor. Rows append to
`artifacts/handler_timing_1_0_0.csv`; session 1's rows stay, so nothing is
lost by stopping and relaunching.

## Two rules that decide whether the session is usable

1. **Repeat every action at least three times, on different words.** This
   plan's own gate says a handler measured once is not measured, and 44 of the
   63 pairs in the 0.28 baseline were single samples. Three is the minimum that
   gives a median.
2. **Open each tab once before you start timing anything on it.** The first
   selection of a tab builds the whole view (1.6 s in the 0.28 baseline) and
   that cost lands on whatever handler you happened to fire. Open the tab, wait
   for it to paint, then work.

Field names below are the grey labels in the left column of the form, so
`sanskrit` means the row labelled `sanskrit`.

---

## A. The four unmeasured shortlist items — the priority

These four were missed by session 1 *and* by the 0.28 baseline, so they have no
before-picture. They are the reason for this session.

### A1. The Sanskrit lookup — all four entry points

One method behind all four; it opens its own database session and runs an
unanchored `LIKE '%part%'` scan per construction part against a 2.26 GB
database. The slowest single thing found by reading, and only three of its four
doors were measured on 0.28.

On **Pass2Add**, with a word loaded, on three different words each:

- click into `sanskrit`, then click away again — that is the focus door and the
  blur door in one pass
- click into `sanskrit`, type anything, press Enter — the submit door
- click into `non_ia`, then click away — the fourth door, and the one never
  measured on 0.28

### A2. The two TSV re-readers

Each rebuilds a manager from a TSV file on **every** event, not once per
session.

- **compound types:** on Pass2Add, click into `construction`, type a
  construction, click away. Three times.
- **phonetic changes:** on Pass2Add, click into `phonetic`. Focus alone is
  enough — this one fires on focus, not blur. Three times.

### A3. The CST book search

Parses a whole CST book. On **Pass2Add**, in the example area:

1. click the eye icon (tooltip "Show Tools") to reveal the search row
2. pick a book in the `book` dropdown
3. type a word into `word to find` and press Enter

Three times, and include one **large** book (a long Nikāya volume) — the cost
scales with the book, so a small one understates it.

### A4. The four subprocess launches

Each shells out to an external application. Close whatever opens before the
next one.

- **Global tab:** `Open Internal Tests` (LibreOffice), then
  `Update Anki Database`
- **Pass2Add:** the pencil icon beside `compound_type` (tooltip "Edit compound
  type rules"), then the pencil beside `phonetic` (tooltip "Edit phonetic
  change rules")

One sample each is acceptable here — the point is whether the window freezes
while the external application starts, which is visible rather than statistical.

---

## B. The keystroke paths — three handlers, 50 ms budget

All three were measured on 0.28 and matter most, because they run while you
type. Type at your normal speed, a **whole word, not one letter**, so the
sample count comes from the typing itself.

On Pass2Add:

- `family_word` — fuzzy-matches against every known word family, per keystroke
- `pattern` — fuzzy-matches against every pattern
- `root_key` — hits the database per keystroke

## C. The pass views' own actions

Session 1 produced exactly one row from the pass views.

- **Pass2Add:** load three different words (this was 438 ms on 0.28), and for
  one of them click `Add to DB`. That is the database write, 496 ms on 0.28 and
  the action where a freeze is least acceptable.
- **Pass1Add, Pass2Pre, Pass2Auto, Pass2x:** open each, load a word, and do
  that view's primary action once. None has ever been measured.
- **Pass2Add:** click into `meaning_1` and click away — runs the relationship
  detector. Then click into `var_phonetic`, type, and click away: this one
  deliberately rewrites `synonym` and `var_text` as a side-effect, so watch
  those two fields change and confirm they are correct.

## D. The Translations tab — the slowest thing measured on 0.28

`Search` there was 1736 ms on the UI thread, the worst number in the baseline,
from a single sample. Search three different terms.

---

## When you are done

Just say so — the log is read from disk, there is nothing to export. Roughly
how long you spent is useful, because it bounds how much of the session was
idle.
