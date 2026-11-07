# Pass1 Auto: unknown words first

## Overview
Pass1 Auto (book run) finds every word that does not resolve to a headword and sends each to the AI. This thread makes it handle the completely unknown words first, then the rest as it does today.

## What it should do
- "Unknown" means the word has no row in the `lookup` table (`Lookup.lookup_key`), or its row holds only an `epd` entry. A row with data in any other column counts as known: headwords, roots, deconstructor, variant, see, spelling, grammar, help, abbrev, abbrev_other, rpd, other, sinhala, devanagari, thai. The user decided on 2026-11-07 that an `epd` entry does not count.
- After the two find-missing steps, split `missing_words_dict` into unknown words and the rest. Rebuild the dict with the unknown words first. Keep the original order inside each group.
- The status line says "Unknown words (not in lookup): N of M" before the loop. Each word's message says "Processing X (unknown)" for the unknown group.
- The paste-text run (`_auto_process_text`) does not change.
- The set of missing words and each word's processing stay the same. Only the order changes.

## Assumptions & uncertainties
Verified this session:
- `lookup` has 1,283,243 rows. 824,230 have no headword. 724,548 have a deconstructor but no headword. 0 rows are completely empty. 79,966 rows hold only an `epd` entry and these now count as unknown. 0 rows hold only an `rpd` entry.
- The loop in `gui2/pass1_auto_controller.py` (`_auto_process_book`) iterates `missing_words_dict` in insertion order. Reordering the dict is enough.
- `is_missing` uses live headword inflections, so a word added in gui2 since the last build is not missing, even if the lookup lacks it. The unknown check runs only on words that are already missing.
Not verified:
- How many words in a real book fall in each group. The user checks this live.
- Lookup keys use binary comparison on the primary key. Words in the CST list are lowercase, so a plain `IN` query should match. The unit test covers this.

## Constraints
- Query the lookup table in chunks (900 keys per `IN`). Do not load all 1.28M keys.
- Contributor server: the database is read-only and has the `lookup` table, so a read query works. Do not write. (Verified locally; the live contributor host has not been checked — assumption.)
- The check is a query for the keys that have data in any column except `epd`. Unknown = chunk words minus those keys.
- Do not mutate ORM objects. Use `session.query(Lookup.lookup_key)`.
- Touched files must pass `ruff check`, `ruff format`, and `pyright --project /dev/null` (gui2 is excluded from plain pyright). Run `just typecheck` before finishing.

## How we'll know it's done
- A unit test with an in-memory `Lookup` table shows unknown words come first and group order is kept.
- The live book run shows the "Unknown words" message, and the first words processed are labelled "(unknown)".
- Existing tests in `tests/gui2/test_pass1_auto_controller.py` still pass.

## What's not included
- The paste-text run.
- New widgets, a new setting, or a change to what counts as missing.
- A change to the prompt or the AI call.
