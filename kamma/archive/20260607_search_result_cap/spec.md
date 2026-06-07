# Spec: Cap gui2 sutta/commentary search results to prevent UI freeze

## Overview
In gui2, searching commentary (and to a lesser extent sutta examples) for a short
term like "sam" returns hundreds of thousands of matches. The commentary search
builds a Flet widget for every match, freezing the UI.

## Current behavior
- Commentary: `BoldDefinitionsSearchManager.search()` (`tools/bold_definitions_search.py`)
  returns `.all()` (no limit); `DpdCommentaryField.choose_commentary()`
  (`gui2/dpd_fields_commentary.py`) renders ALL results → freeze.
- Sutta: `find_cst_source_sutta_example()` (`tools/cst_source_sutta_example.py`)
  returns all matches, but `DpdExampleField.choose_example()`
  (`gui2/dpd_fields_examples.py:362`) already renders only `[:50]` — no freeze,
  but no notice that results were truncated.

## What it should do
- Never build UI for more than a fixed cap (50) of results.
- For commentary, also stop the DB from fetching the whole result set.
- When results are truncated, show a clear notice in the dialog telling the user
  to refine their search.

## Assumptions & uncertainties
- 50 is the chosen cap (matches the existing sutta limit). Confirmed with user.
- Detecting "there are more" via `CAP + 1` fetch (commentary) / `len() > CAP`
  (sutta) is sufficient; no exact total count needed.
- `process_bold_tags` / `highlight_word_in_sentence` are unaffected — we only
  change how many rows are built.

## Constraints
- MUST preserve existing behavior of `BoldDefinitionsSearchManager.search()` for
  `exporter/webapp/main.py:206` (no limit there) → new `limit` param defaults to
  `None`.
- MUST NOT add a hard limit to `find_cst_source_sutta_example` —
  `exporter/analysis/book_to_verses.py:40` and `passage_by_code.py:186` call it
  with `"."` to match ALL verses and rely on full results.
- Index alignment of checkbox `data` / radio `value` into the full result list
  must stay correct (`click_choose_example_ok`, `update_example_index`).

## How we'll know it's done
- Searching commentary for "sam" returns near-instantly, shows ≤50 entries plus a
  "refine your search" notice, and does not freeze.
- Searching sutta for a common term shows ≤50 entries plus the notice.
- `uv run pytest` for related tests passes; webapp + analysis callers unaffected.

## What's not included
- Real pagination / "load more". A hard cap + refine-search message is enough.
- Changing the regex/search semantics themselves.
