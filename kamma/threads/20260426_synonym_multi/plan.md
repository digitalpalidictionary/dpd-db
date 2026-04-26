# Plan — add_synonym_multi.py

## Architecture Decisions
- **Separate file, not refactor.** User chose option 1 to keep `add_synonym_single.py` untouched. Mild duplication of the prompt/commit block is the accepted tradeoff.
- **Inverted-index grouping.** Within each `(pos, sig)` bucket, build `meaning → set[headword_id]`, then for each headword pair sharing ≥2 meanings, group them. Cheaper and clearer than naive O(n²) per bucket.
- **Exception key format `pos:sorted_meanings_joined_by_|:sig`.** `|` separator avoids collision with single-script keys (which use `:` only) and with meanings that contain `:`.
- **Skip `meaning_1` without `"; "`.** Strict separation from the single-meaning script — chosen by user.
- **Include `pron` and `sandhi`.** Same approach as the single script: grammar_signature enforces grammar match. Be ready to revert (add `pos not in {"pron","sandhi"}` filter) if noisy.
- **Reuse the single script's commit math verbatim** (set unions/differences for syn/var/phonetic) — proven and correct.

## Phase 1 — Build the script

- [x] Create `db_tests/single/add_synonym_multi.py` with module docstring, imports, and `GlobalVars` class mirroring `add_synonym_single.py` (db session, exceptions load/save).
  → verify: `uv run python -m py_compile db_tests/single/add_synonym_multi.py` exits 0. ✓

- [x] Add helpers: `clean_meaning`, `grammar_signature`, `_split_field`, `existing_synonyms`, `existing_phonetic_variants`, `_format_fields`, `_show_result` — copied/adapted from `add_synonym_single.py`.
  → verify: `uv run ruff check db_tests/single/add_synonym_multi.py` reports no errors. ✓

- [x] Implement `find_multi_meaning_groups(g)`:
  - Iterate `g.dpd_db`, filter to rows where `meaning_1` contains `"; "`.
  - Build per-row cleaned meaning set and `(pos, sig)` bucket.
  - Within each bucket, build inverted index `meaning → list[hw]`.
  - For each headword pair in the bucket, compute `shared = meanings_a & meanings_b`; if `len(shared) >= 2`, register an edge.
  - Merge edges transitively (union-find or simple BFS) so a triple sharing the same pair of meanings appears once per group.
  - Build exception key per group; skip if in exceptions.
  - Store as `g.groups: dict[str, tuple[list[DpdHeadword], list[str]]]` (key → (headwords, sorted shared meanings)).
  → verify: import check passed ✓

- [x] Implement `prompt_groups(g) -> bool` mirroring the single script.
  → verify: ruff clean; imports ok ✓

- [x] Implement `main()` with `pr.tic()` / `pr.toc()` and the restart loop identical to `add_synonym_single.py`.
  → verify: import check passed ✓

- [x] Phase verification: ruff and py_compile both pass ✓
