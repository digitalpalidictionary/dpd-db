# Plan: pass2x_in_commentary (data proof, TUI only)

## Architecture Decisions
- **Dedicated package folder `gui2/pass2x/`** holds all Pass2x code now and later. This thread adds one read-only TUI module: **`gui2/pass2x/in_commentary_tui.py`** (plus `gui2/pass2x/__init__.py` if needed for imports). Later threads add the controller/view/file-manager siblings here. No Flet code in this thread.
- **Simplified matching (2026-06-16).** No `DatabaseManager`, no `Lookup`, no deconstructor. The script builds one map `inflected form → [incomplete headwords]` directly from `DpdHeadword.inflections_list_all` (for headwords where `gui2.needs_example.is_missing_sutta_example` is True) via `get_db_session`. A commentary word is a candidate iff it is a key in that map. Deconstructor lookup and the variant/spelling exclusions are left as comments to re-activate later. Use `tools.clean_machine.clean_machine` for word cleaning.
- **Corpus built once.** The translations-db search builds an in-memory structure a single time (list of rows or an inverted word→rows index), then answers all candidate lookups from it — never a per-word full-db scan.
- **Pure functions + small `main()`.** Each stage (harvest, clean, gate, resolve, corpus-build, search, display) is a standalone, testable function.
- **Output via `tools.printer`** for the summary; bolding via terminal ANSI so the marked word is visible.
- **Numbered step TSVs** (added at user request, 2026-06-16) written to `gui2/pass2x/data/` (gitignored): `step1_harvested_words.tsv`, `step2_candidates.tsv`, `step3_resolved_headwords.tsv`, `step4_example_sentences.tsv` — **one row per word**, all examples collapsed into a single `examples` column, matched word wrapped in `**…**`.

### Run results after corrections (2026-06-16)
- Predicate corrected to `not (meaning_1 and source_1)` (commentary examples count as done; `ṭhātukāma`-style headwords excluded). Exceptions list applied. Commentary-of-origin shown as example #1.
- 24,667 commentary rows → 88,273 words harvested → **18,374 matched** (was 22,532 before the predicate fix; 26 removed by the exceptions list) → step 1–3 in **3.3s**, step 4 (422,484 rows scanned) in **10.7s**. 280 matched words had no translation paragraph (they still get the commentary example).

## Phase 1 — Candidate finding (no translations db yet)

- [x] Create `gui2/pass2x/` folder (with `__init__.py` if imports need it) and `gui2/pass2x/in_commentary_tui.py` skeleton: imports, `main()` with `pr.tic()`/`pr.toc()`, instantiate `DatabaseManager`, call `make_pass2_lists()` + `get_all_decon_no_headwords()`.
  → verify: `uv run ruff check gui2/pass2x/in_commentary_tui.py` passes; runs and prints the two set sizes.

- [x] Implement `harvest_commentary_words(db_session) -> set[str]`: query all non-empty `commentary` values; for each, drop `-` placeholders, strip leading `(CODE)` prefix, remove `<b>`/`</b>` tags, `clean_machine(..., niggahita="ṃ")`, split, add hyphenated parts. Return the deduped word set.
  → verify: print total commentary rows used and harvested word-set size; eyeball that `<b>` tags and `(SNPa)`-style prefixes are gone on a few samples.

- [x] Implement `gate_candidates(words, db, variants, spelling) -> set[str]`: keep `W` if `(W in db.all_inflections_missing_example or W in db.all_decon_no_headwords)` and not in variants/spelling dicts.
  → verify: print pre-gate and post-gate counts.

- [x] Implement `resolve_candidates(words, db) -> dict[str, list[DpdHeadword]]`: for each gated `W`, `db.get_headwords(W)`; keep only those with ≥1 result.
  → verify: print resolved-candidate count; print 3 examples where resolution came via the **deconstructor/component** path (ids empty → deconstructor_unpack non-empty) to prove the not-exact path works.

**Phase 1 checkpoint:** report harvested / gated / resolved counts and a few deconstructor-path examples. (Report-only; no commit pause.)

## Phase 2 — Translation-sentence sourcing + display

- [x] Implement `build_translation_corpus(db_path) -> <index>`: enumerate tables via `sqlite_master`; in one pass collect `(source_table, paranum, pali_text, english_translation)` rows, normalising niggahita on `pali_text` to match the harvested form. Choose structure (flat list vs inverted word index) based on what keeps per-word lookup fast.
  → verify: print table count, total row count, corpus build time, and how many rows have empty `english_translation`.

- [x] Implement `find_example_sentences(word, corpus) -> list[tuple[str, str, str, str]]`: whole-word match of `word` in `pali_text`; return `(source, paranum, pali_bolded, english)`; bold the matched word.
  → verify: per-word lookup time is small; spot-check a known commentary word returns sentences with the word correctly bolded.

- [x] Implement `display(resolved, corpus)`: for each candidate print word → incomplete headwords (`lemma_1`, `pos`, `meaning_combo`) → numbered Pāḷi(bolded)+English sentences. Report words with **zero matched sentences** and words whose matches have **zero English**, rather than dropping them.
  → verify: output readable; the niggahita/match-quality and English-coverage risks are visible.

- [x] Final summary in `main()` via `pr.summary(...)`: harvested / gated / resolved counts, corpus build + search timing, count of candidates with zero matches, count with zero-English matches.
  → verify: `uv run gui2/pass2x/in_commentary_tui.py` completes; numbers reconcile; spot-checks pass.

**Phase 2 checkpoint:** present the full run output so we can judge match quality and performance, and decide what (if anything) to change before the GUI thread.

### Checkpoint findings (2026-06-16 run)
- Pipeline works end-to-end. Phase 1 ≈150s, Phase 2 ≈12–47s, 422,484 rows scanned. Harvested 88,273 → gated 45,706 → resolved 42,860 (20,376 via deconstructor). Only 21 candidates have zero-English matches → English coverage is excellent. Match + niggahita-flexible bolding are accurate on real words (`nakhādīhi`, `olambamānāhi`, `pāvusakāle`).
- **Finding A — granularity:** the translations DB is **paragraph-level**, so each "example" is a whole paragraph (avg ~1857 chars), not a sentence. English is aligned per-paragraph. Tightening to one sentence would lose clean English alignment. **Decision needed.**
- **Finding B — common-word noise:** the gate admits ultra-common particles that are technically incomplete headwords (`ca` 82k hits, `na`, `ti`, `vā`, `taṃ`, `so`, `hi`…), bloating output and matching junk like `(a. ni. 3.66)`. Real targets are rarer inflected forms. **Decision needed:** filter by min length / frequency cap / particle stoplist?
- Diagnostic step TSVs are large (row-count driven); `gui2/pass2x/data/` is gitignored.

## Out of scope (future threads)
- Pass2x tab + "in commentary" button (Flet).
- yes/no/pass choices + file-manager persistence.
- Downstream pass2auto wiring / AI.
