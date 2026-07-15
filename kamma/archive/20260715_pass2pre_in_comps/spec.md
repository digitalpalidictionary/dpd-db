# Spec: pass2pre "in comps" — surface compound components needing examples

## Overview

Pass2Pre (gui2 → Pass2PreProcess tab) currently builds a queue of words from a
book's text that are missing sutta examples. This thread adds an optional
"in comps" mode (a switch next to the "PreProcess Book" button) that goes one
step deeper: every book word that resolves to a **compound headword** whose
components are missing examples becomes a work item — **the compound itself,
one at a time**. The user sees sentences containing the compound and decides,
for each missing-example component headword, whether that sentence is a valid
example of the component (seen inside the compound).

Example: book contains "assakhaluṅka" (grammar contains "comp", construction
`assa + khaluṅka`). "khaluṅka" is missing an example, so "assakhaluṅka" is a
work item displayed as `[assakhaluṅka] khaluṅka`; its examples are sentences
containing "assakhaluṅka", and the headwords offered include "khaluṅka".

(Redesigned 2026-07-15: originally components were queued as their own work
items — first appended at the end, then interleaved, then with batched parent
compounds. All wrong: the user needs ONE compound at a time as the work item,
with its missing components reviewed against that compound's sentences.)

This surfaces tens of thousands of extra candidates, which is why it is
opt-in via the switch (default off).

## Current behaviour (files involved)

- `gui2/pass2_pre_controller.py` — `find_words_with_missing_examples()` builds
  `missing_examples_dict` (insertion-ordered = processing order) from
  `all_cst_words` + SC words, filtered by `is_missing_example()`.
- `gui2/database_manager.py` — `make_pass2_lists()` derives
  `all_inflections_missing_example` and `all_suffixes` from the cached corpus.
  `get_headwords(word)` resolves a word via `Lookup` to headwords that are
  missing examples. Words in `Lookup` with deconstructions but no headwords
  are already handled (`all_decon_no_headwords` / `get_headwords_from_deconstructor`).
- `gui2/pass2_pre_view.py` — UI; `handle_book_click` starts the run;
  `get_cst_examples()` in the controller searches CST with `\bword\b`.
- `db/models.py` — `DpdHeadword.construction_line1_clean_list` splits the
  cleaned first construction line on ` + ` (phonetic changes already stripped).

## What it should do

1. **UI switch** — an `ft.Switch(label="in comps", value=False)` in the top row
   of `Pass2PreProcessView`, next to the "PreProcess Book" button.
2. **Component discovery (only when switch is on)** — after the normal
   `make_all_words_dict()` + `add_sc_words()` steps:
   - Build (in `DatabaseManager`, derived from the cached corpus) a mapping of
     inflection → compound components, covering every headword whose `grammar`
     matches `\bcomp\b` and whose `construction_line1_clean_list` has ≥ 2 parts.
     Components exclude suffixes (`all_suffixes`), mirroring
     `get_related_headwords()`.
   - For every book word (CST + SC), **in text order**, check its components
     with `is_missing_example()`. If any are missing, record
     `comps_components[compound] = missing components` and queue the
     compound at that position (`setdefault`, `[]` segments).
   - The compound's own status is **irrelevant**: with an example, without,
     already matched/unmatched — it becomes a work item either way. The only
     gate is on the component: still missing an example and not yet decided
     on (matched/unmatched as the component word). This is what lets the
     user dig through ALL the words of a text and converge: every Yes/No on
     a component removes it from all future queues. (2026-07-15: earlier
     versions wrongly skipped processed compounds and dumped
     example-having compounds at the end of the queue.)
   - One level only: no recursion into components that are themselves compounds.
3. **Headwords and examples per work item** — examples are always fetched
   with the normal `\b{word}\b` regex (the work item IS the compound, so no
   special regex mode). Headwords for an entry
   (`get_entry_headwords()`) are the compound's own missing-example
   headwords (as today) **plus** the missing-example headwords of each
   component in `comps_components`, deduplicated by id. The word-in-text
   field updates **per headword** (`display_word_in_text()` called in
   `load_next_headword()`): plain `compound` for the compound's own
   headwords, `[compound] sub word` for a component's. The sentence
   highlight (`highlight_term_for()`) is the **sub word**, not the
   compound; if not found in the sentence, letters are stripped from its
   end until it matches (sandhi at the join).
4. Everything downstream (Yes/No/New/Pass, file manager, daily log, counters)
   works unchanged for component words.

## Assumptions & uncertainties

- Components in `construction_line1_clean_list` are clean stems (e.g. "assa")
  and are generally present in `Lookup`/inflection sets, so the existing
  `is_missing_example()` + `get_headwords()` machinery handles them without a
  separate lemma-based lookup. Components not found anywhere are skipped by the
  existing empty-headword skip logic in `load_next_word()`.
- The inflection→components map is built lazily only when the switch is on
  (it's a full-corpus pass; corpus is already cached in `DatabaseManager`).
- All queue entries use the exact `\bword\b` example search; in-comps mode
  only adds compound work items and extends their headword list.
- A **Yes** on a component headword is recorded in `matched` keyed by the
  **component word** (`current_source_word()` via `entry_headword_sources`)
  — the sub word genuinely got its example, so it stops surfacing anywhere.
- A **No** on a component headword is recorded in `unmatched` keyed by the
  **pair** `"{compound} + {sub word}"` (`current_unmatched_key()`): "not a
  match in THIS compound". The queue gate in `add_comps_entry()` checks the
  pair, so that compound never asks again, but other compounds containing
  the same sub word still surface it in their own sentences. (Keying the
  bare sub word would hide it from every other compound after one No;
  keying the compound would overwrite the compound's own decision.) The
  ` + ` pair keys are inert for other consumers of `unmatched`
  (`in_commentary_controller`, `pass2pre_an_counts`): they check plain book
  words against the keys, and a key containing ` + ` never equals a plain
  word.
- SC word segments: components discovered from SC compound words get CST
  examples fetched like any word without preloaded segments (empty list →
  `get_cst_examples()`).
- The switch is session-only state; not persisted to config.

## Constraints

- Follow existing gui2 patterns (controller/view split, derived sets in
  `DatabaseManager` gated by `_corpus_gen`).
- No changes to `db/models.py` or the database.
- Touched files must pass `ruff check`, `ruff format`, `pyright`
  (note: gui2 is pyright-excluded but not ruff-excluded).

## How we'll know it's done

- Switch off: behaviour is byte-identical to today (no extra words queued).
- Switch on: a compound whose component is missing an example appears as one
  work item `[compound] component`, showing only sentences containing the
  compound, and offering the component's headwords for Yes/No decisions.
- Unit tests for the new pure logic (component-map building, queue ordering).

## What's not included

- Recursion into nested compounds.
- Persisting the switch state.
- Any change to pass2 auto / pass2x flows.
- Performance work beyond the lazy one-pass corpus derivation.
