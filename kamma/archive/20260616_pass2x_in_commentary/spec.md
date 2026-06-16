# Spec: pass2x_in_commentary (data proof, TUI only)

## GitHub issue
#162 — gui2 improvements

## The bigger vision (what this is part of)
The end goal is a new **Pass2x** tab in gui2, sitting between **Pass2pre** and **Pass2auto**, that hosts a growing set of buttons for finding words that still need an example sentence. The first button is **"in commentary"** (more buttons will follow later).

The full "in commentary" feature, once complete, will:
1. Harvest words from the `commentary` column that are inflections (or deconstructed components) of headwords still missing a sutta example — reusing the same matching/deconstruction logic as Pass2pre.
2. For each word, show a **selectable** list of Pāḷi sentences it occurs in, each with its English translation, with the word **bolded** for quick scanning.
3. Offer the same three choices as Pass2pre: **yes** (this sentence is the example), **no** (not in any example), **pass** (deal with later).
4. Feed the "yes" results into the **same downstream processing path that Pass2auto** uses to complete the headword.

This is being built deliberately in stages because it is complex and the data behaviour may force changes along the way. **This thread is stage 1: prove the data in a read-only TUI before any GUI is built.** Choices, persistence, the Pass2x tab itself, and the Pass2auto wiring are explicitly later threads (see "What's not included").

## Overview
First slice of the **Pass2x → "in commentary"** feature described above. This thread builds **only the data pipeline, proven in a read-only TUI/script** — no Flet, no new tab, no persistence of choices, no AI. The goal is to validate match quality and performance of the data before any GUI is built.

The pipeline finds words appearing in the `commentary` column of `dpd_headwords` that are inflected forms (or deconstructed components) of headwords still missing a sutta example, and for each shows the Pāḷi example sentences it occurs in (with English) from the translations database, with the word bolded.

## Decisions locked (from user)
1. **Word source** = `DpdHeadword.commentary` column (`db/models.py:1048`), harvested across all rows.
2. **Example-sentence search scope** = **all tables** in `resources/tipitaka_translation_db/tipitaka-translation-data.db` (mūla / KN / vinaya included, not only `_att`/`_tik`), because bolded commentary words appear in mūla texts too (fewer than in att/tik).
3. **Scope of this thread** = data only, in a TUI. GUI tab, choices (yes/no/pass), persistence, and downstream pass2auto wiring are deferred to follow-up threads.

## Simplification (2026-06-16, after first runs)
To reduce complexity and see clean results first, the implementation was cut back to the smallest useful core:
- **Deconstructor/compound lookup is REMOVED for now** (left as a comment to re-activate later). A commentary word is matched **only** if it is a direct inflected form, i.e. it appears in some incomplete headword's `inflections_list_all`.
- Matching no longer goes through `DatabaseManager.get_headwords` / the `Lookup` table; instead the script builds one map `inflected form → [incomplete headwords]` directly from `DpdHeadword.inflections_list_all` where `is_missing_sutta_example` is True.
- The known-variant and spelling-mistake exclusions are also dropped for now (noted in code).
- `step4_example_sentences.tsv` is **one row per word**, with all of that word's example paragraphs collapsed into a single `examples` column (each truncated).

The detailed steps below remain the eventual target; the deconstructor parts are deferred, not abandoned.

## Corrections (2026-06-16, second round of feedback)
- **"Incomplete" predicate fixed.** Pass2x must NOT reuse `is_missing_sutta_example` — that rule (from Pass2pre, which hunts *sutta* examples) treats a commentary-only example as still-missing. Here we are looking FOR commentary examples, so an existing example of any kind (incl. commentary) means done. Correct rule: a headword is incomplete iff **not (`meaning_1` and `source_1`)**. Example: `ṭhātukāma` (id 81184) has `meaning_1` + `source_1=DNa21.10`, so it is complete and must be excluded — the old rule wrongly re-included it. New incomplete count ≈ 36,392 headwords.
- **Exceptions list.** Over-eager matches (common particles, single letters) are filtered via an importable/exportable list: `gui2/pass2x/in_commentary_exceptions.txt` (one word per line, committed) managed by `gui2/pass2x/in_commentary_exceptions.py` (`InCommentaryExceptions` — `load`/`save`/`add`/`in`). Seeded with the obvious particles; the user curates it.
- **Example #1 is the commentary the word was pulled from.** Harvest records, per word, the first `DpdHeadword.commentary` entry it appeared in; that commentary is shown as example #1, ahead of the translation-db paragraphs.
- **Step 3 keeps multiple headwords per word** (one word → many incomplete headwords; e.g. `kappanaṃ` → 11).

## What it should do
1. **Harvest commentary words.**
   - Query all non-empty `commentary` values from `dpd_headwords`.
   - Clean each value: drop `-` placeholders; strip a leading source-code prefix like `(SNPa)`; remove `<b>`/`</b>` tags; then run `tools.clean_machine.clean_machine` (niggahita `"ṃ"`), splitting into words and adding hyphenated parts (mirror `make_cst_text_list`'s approach).
   - Collect into one `set[str]` of candidate words.

2. **Build the pass2 filter sets** by reusing `gui2.database_manager.DatabaseManager`:
   - `make_pass2_lists()` → `all_inflections_missing_example` (inflections of headwords where `is_missing_sutta_example` is True).
   - `get_all_decon_no_headwords()` → `all_decon_no_headwords` (lookup keys with `headwords == ""` and `deconstructor != ""`).
   - Load `VariantReadingFileManager` and `SpellingMistakesFileManager` to exclude known variants / spelling mistakes (mirror `Pass2PreController.is_missing_example`).

3. **Candidate gate.** Keep commentary word `W` if
   `(W in all_inflections_missing_example or W in all_decon_no_headwords)`
   and `W not in variants_dict` and `W not in spelling_mistakes_dict`.

4. **Resolve to incomplete headwords.** For each gated `W`, call `db.get_headwords(W)` — unchanged. This already handles:
   - **exact inflection** → `Lookup.headwords_unpack` ids → headwords filtered by `is_missing_sutta_example`; and
   - **not an exact inflection** (compound/sandhi only in the deconstructor) → empty ids → `get_headwords_from_deconstructor` → `deconstructor_unpack` split into components → **recursive `get_headwords()` per component**.
   Keep only `W` that resolve to ≥1 incomplete headword.

5. **Example sentences from the translations db.**
   - Enumerate all tables via `sqlite_master`.
   - For each candidate `W`, find rows whose `pali_text` contains `W` as a whole word (word-boundary match) and return `(table/source, paranum, pali_text, english_translation)`.
   - Bold `W` in the Pāḷi sentence.
   - **Performance:** build the searchable corpus once (single in-memory pass over all tables, or an inverted index keyed by word), NOT a per-word scan of the whole db. Measuring this is a primary goal of the TUI.

6. **Display (TUI).** For each candidate: the word → its incomplete headwords (`lemma_1`, `pos`, `meaning_combo`) → a numbered list of example sentences (Pāḷi with the word bolded + English). Read-only; nothing is written or persisted.

## Assumptions & uncertainties
- The commentary source-code prefix is always a parenthesised code at the very start, e.g. `(SNPa) ...`; `<b>...</b>` wraps the example word(s). Both are stripped before tokenising. **To verify against real data.**
- "Incomplete headword" is exactly `is_missing_sutta_example` — no separate meaning_1/source_1 logic is reimplemented; the existing helper already encodes "no example, or only late/commentary examples, or no meaning_1".
- All translation-db tables share the schema `(id, rend, paranum, pali_text, ..., english_translation)`; `english_translation` is the same row as `pali_text` (no cross-row alignment needed). English coverage sampled ~99% in `s0101a_att`, but coverage across mūla tables is **unmeasured** — the TUI must surface words with zero English.
- **Niggahita mismatch risk:** `commentary` cleaning normalises niggahita to `"ṃ"`, but `pali_text` in the translations db may use `"ṁ"` or a different cleaning. Both sides must be normalised the same way before matching. This is the main match-quality risk the TUI exists to expose.
- Searching ~hundreds of tables / 800 MB for every candidate is the main performance risk; corpus is built once.

## Constraints
- **Read-only.** No db writes, no Flet, no new GUI tab, no JSON persistence, no AI calls.
- Reuse existing logic verbatim where it exists: `DatabaseManager.get_headwords`, `is_missing_sutta_example`, `clean_machine`, the variant/spelling file managers. Do not fork or reimplement the deconstruction logic.
- Modern type hints, `pathlib.Path`, `from icecream import ic` if needed, `tools.printer` for output, no `sys.path` hacks.
- Everything Pass2x lives in its own package folder **`gui2/pass2x/`** so later GUI files (controller, view, file manager) join it there. This thread adds only the read-only TUI module inside it; imports work from project root.

## How we'll know it's done
- `uv run <script>` runs to completion with no errors and prints, for a sample of candidates: the word, its incomplete headwords, and bolded Pāḷi + English example sentences.
- A summary prints: total commentary words harvested, count after the candidate gate, count resolving to ≥1 incomplete headword, and timing for corpus build + search.
- Spot-checks confirm at least a few candidates resolve via the **deconstructor/component** path (not just exact inflections), demonstrating the not-exact path works.
- The niggahita/match-quality and English-coverage risks are observable in the output (e.g. words with zero matched sentences and words with zero English are reported, not silently dropped).

## What's not included
- No Pass2x tab, no "in commentary" button, no Flet UI.
- No yes/no/pass choices, no file managers, no JSON output for downstream.
- No pass2auto wiring, no AI, no db writes.
- No new automated tests beyond a quick verification run (this is an exploratory data-proof script, mirroring the `verb_finder` precedent).
