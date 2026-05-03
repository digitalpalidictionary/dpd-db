# Spec: Fix multi-match overwrite in find_sentence_example

**GitHub Issue:** #232 — Finding examples in GUI miss paragraphs.

## Overview

When a search word appears more than once within a single `<p>` paragraph in the CST XML,
`find_sentence_example` returns only the *last* matching sentence. All earlier matches are silently
discarded. This causes the GUI (Pass2Add) to miss valid sutta examples for many words.

## What it should do

- For every sentence within a `<p>` paragraph that contains `text_to_find`, emit a separate
  `(prev_sentence + sentence + next_sentence)` example.
- The outer loop in `find_cst_source_sutta_example` must append one `CstSourceSuttaExample` per
  collected example, keeping existing dedup logic.
- A word that appears only once still produces exactly one result (no regression).
- The gāthā path (`find_gatha_example`) is updated to write into the same list structure for
  consistency, even though its own internal logic is unchanged.

## Confirmed reproduction cases

- `an1` search for `āvilattā`: paragraph #45 of `s0401m.mul.xml` contains both
  `āvilattā, bhikkhave, udakassa.` and `āvilattā, bhikkhave, cittassāti.` — only the latter
  was returned.
- `vin2` search for `theyyasatthasaññī`: paragraph #410 of `vin02m1.mul.xml` contains four
  matching sentences — only the last (`atheyyasatthasaññī anāpatti.`) was returned.

## Affected files

- `tools/cst_source_sutta_example.py`
  - `find_sentence_example` (line ~350)
  - `find_gatha_example` (line ~293)
  - `find_cst_source_sutta_example` — `g.example` reset and append site (lines ~2784, ~2940)
  - `GlobalData` — `self.example` type annotation (line ~179)

## Assumptions & uncertainties

- `g.example` is only read at the single append site within this file. (Confirmed by grep — no
  external callers read `g.example` directly.)
- `find_gatha_example` already handles single-stanza matches correctly; only its write contract
  needs updating to use a list.
- The fix is purely additive: more results may be returned where the word appears N times in one
  paragraph; no existing single-match cases are affected.

## Constraints

- Do not alter `find_gatha_example` internal gāthā-stitching logic.
- Preserve dedup on `(source, sutta, example)`.
- Do not refactor unrelated code.

## How we'll know it's done

- `an1` / `āvilattā` returns 2 distinct examples (udakassa + cittassāti).
- `vin2` / `theyyasatthasaññī` returns all matching sentences from paragraph #410.
- Existing `__main__` test (`vin5` / `adhipātimokkh`) produces the same or more results.

## What's not included

- Changes to `split_sentences`, `clean_example`, or any gāthā logic.
- Fixing any other cause of missing examples beyond the overwrite bug.
