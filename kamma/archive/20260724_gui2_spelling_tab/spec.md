# Spec: gui2 "sp" spelling find/replace tab

## Overview
Add a new tab to gui2, labelled **"Sp"**, that does regex find/replace across the
**English prose fields** of `dpd_headwords`. It mirrors the existing `'` tab
(`SandhiFindReplaceView`), which does the same job for Pāḷi fields, with three
deliberate differences: it targets English fields, it treats the Find term as a
**raw regex** (so `\b`, character classes and backreferences work), and there is
**no Phase 2** (English fields carry no bold/italic tags).

Primary use case: replace British spellings with US spellings, e.g. `cognise` →
`cognize` — but only as a whole word (`\bcognise\b`), because "cognise" otherwise
only appears inside "recognise". Regex is what makes this safe.

## What it should do
1. New tab labelled **"Sp"**, placed after the existing `'` tab (see Constraints).
2. Two inputs: **Find** (regex) and **Replace**, plus **Find** and **Clear** buttons,
   and a **strip** switch (default on, trims both inputs — mirrors the `'` tab).
3. On Find:
   - Treat Find as a raw Python regex (NOT escaped). If the regex fails to compile,
     show an error message and do nothing.
   - Query `dpd_headwords` for rows where any of the four English fields matches the
     pattern via SQLite `regexp_match` (verified to support `\b` on the live db).
   - Fields searched, in order: `meaning_1`, `meaning_2`, `meaning_lit`, `notes`.
4. Walk the results **one field at a time** (headword → field), skipping fields with
   no live Python-regex match:
   - **Found**: show the field text with every match highlighted.
   - **Replaced**: show the field text after `re.sub(pattern, replace, text)`, with
     every replacement highlighted (built via `match.expand(replace)` so
     backreferences like `\1` work).
   - Show a context/counter line: which entry (`lemma_1` + `id`), which field,
     position N of M.
5. Two actions per field:
   - **Commit** — apply `re.sub(pattern, replace, text)` to that field (all matches
     at once), write the field back, `db.commit()`, `mark_corpus_stale()`, advance.
   - **Ignore** — leave the field unchanged, advance.
6. When a headword's fields are exhausted, move to the next headword; at the end,
   reset to a clean state.

## Highlighting (regex-safe)
Do NOT use `re.split(pattern, text)` for highlighting — a Find pattern with capturing
groups would make `re.split` emit the group contents and corrupt the spans. Build the
Found and Replaced spans from a single `re.finditer(pattern, text)` pass instead:
emit the text between matches, then a highlighted `match.group(0)` (Found) or
highlighted `match.expand(replace)` (Replaced). The Replaced preview therefore equals
the `re.sub` result that Commit applies — preview and commit are guaranteed identical.

## Assumptions & uncertainties
- **Fields are exactly** `meaning_1`, `meaning_2`, `meaning_lit`, `notes` — the only
  free-text English prose columns on `DpdHeadword`. (`antonym`/`synonym`/`variant`
  hold bare lemma lists, not English, so they're excluded — confirmed via models.py.)
- `regexp_match` works on the live db and supports `\b` — **verified** against
  `dpd.db` (`cognise`→15 hits, `\bcognise\b`→0, `\bthe\b`→7399).
- The DB `regexp_match` is only a pre-filter to pick candidate rows; Python's `re` is
  the source of truth for highlighting/replacement, so any minor divergence between
  SQLite regexp and Python regexp only risks a candidate row showing zero live matches
  (harmless — it's just skipped, hence step 4 skips no-match fields).
- Committing per field (immediate `db.commit()`) matches the `'` tab's habit.
- New view file will be `gui2/spelling_find_replace_view.py` /
  `SpellingFindReplaceView` — the existing `gui2/spelling.py` is the unrelated
  spell-checker gate; no collision.

## Constraints
- Follow the existing `SandhiFindReplaceView` structure and gui2 conventions.
- Place the new tab **immediately after `'`** (index 9) in `tab_labels` /
  `_view_builders`, renumbering the subsequent tabs (Sandhi…CT shift down by one) and
  the `_warmup_tab_order` indices to match. (User chose visual adjacency over the
  no-renumber option.)
- Modern type hints; `Path` from pathlib; no comments explaining *what*.
- Only mutate the ORM field when actually committing a replacement (project ORM rule).
- Must pass `ruff check`, `ruff format`, `pyright` on every touched file.

## How we'll know it's done
- The "Sp" tab appears and builds without error; existing tabs (esp. `'`/Sandhi) are
  unaffected — their indices are unchanged.
- Find `\bcognise\b`, Replace `cognize`: previews each affected field with the whole
  word highlighted; Commit rewrites the field; Ignore skips it; "recognise" is never
  touched.
- An invalid regex shows an error instead of crashing.
- Lint/format/type checks pass.

## What's NOT included (deferred)
- The `'` tab's Phase 2 bold/italic-tag search — English fields have no such tags.
- Per-occurrence accept/reject within a field, and an "exceptions" / persistent skip
  list — a later phase if needed.
- Root-table English fields (`root_meaning`, `root_example`) — out of scope.
