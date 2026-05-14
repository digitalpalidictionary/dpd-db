# Plan: Book Code Translator

## Architecture Decisions
- **Row key = CST filename stem.** Only field 1:1 with all others. Gui/dpd codes fan out.
- **TSV co-located with module** in `tools/` (matches `tools/ipa.py` + `tools/ipa.tsv`, `tools/compound_type_manager.py` + `tools/compound_type_manager.tsv`).
- **Generation script is one-shot.** Phase 1 produces `tools/cst_book_translator.tsv` by merging existing dicts; thereafter the TSV is hand-edited. Lives in `scripts/build/`.
- **No migration in this thread.** Prove translator works in isolation first.
- **`translate()` auto-detect order:** exact match against by_filename → by_gui (lowercased) → by_dpd (preserved case lookup with case-insensitive fallback) → by_book_name (case-insensitive). Empty list on no match.

## Phase 1 — Generate canonical TSV
- [ ] Write `scripts/build/generate_books_tsv.py` that imports `cst_texts` (`tools.pali_text_files`), `book_codes` (`gui2.dpd_fields_examples`), and `file_list` (`db.bold_definitions.functions`); merges them keyed by CST filename stem; derives `cst_book_name` from the `book_codes` display string by stripping the leading code prefix (e.g. `"DN1 "`) and prepending the nikāya derived from the DPD code; writes `tools/cst_book_translator.tsv`.
  → verify: run the script, inspect `tools/cst_book_translator.tsv` for: row count > 100, header row present, `s0101m.mul` row has `gui_book_code=dn1` and `dpd_book_code=DN`, `s0101a.att` row has `dpd_book_code=DNa`, `kn14` appears in two rows (s0513m.mul, s0514m.mul).
- [ ] Spot-check 5 rows from different nikāyas (vinaya, dn, abhidhamma, ṭīkā, aññā) for sensible `cst_book_name`; fix generator if a class of rows is wrong.
  → verify: visual inspection of TSV.

## Phase 2 — Build the translator
- [ ] Create `tools/cst_book_translator.py` with `BookInfo` dataclass and module-level `_load()` reading `tools/cst_book_translator.tsv` once into three dicts (by_filename, by_gui, by_dpd) plus the full list.
  → verify: `uv run python -c "from tools.book_translator import all_books; print(len(all_books()))"` prints expected row count.
- [ ] Add `from_cst_filename`, `from_gui_code`, `from_dpd_code`, `from_cst_book_name`.
  → verify: REPL — `from_cst_filename("s0101m.mul").gui_book_code == "dn1"` and `len(from_gui_code("kn14")) == 2`.
- [ ] Add `translate(value)` with auto-detect.
  → verify: REPL — `translate("DN")`, `translate("dn1")`, `translate("s0101m.mul")`, `translate("Dīghanikāya, Sīlakkhandhavaggapāḷi")` all return non-empty.
- [ ] Add `cst_xml_path` property using `tools.paths.ProjectPaths`.
  → verify: path ends with `resources/dpd_submodules/cst/romn/s0101m.mul.xml` and exists.

## Phase 3 — Tests
- [ ] Create `tests/tools/test_book_translator.py` covering known-good round-trips, fan-out (`kn14`, `VINa`), case-insensitive matches, unknown inputs return `None`/`[]`, `translate()` dispatch, `cst_xml_path` existence.
  → verify: `uv run pytest tests/tools/test_book_translator.py -v` all pass.
- [ ] Run ruff.
  → verify: `uv run ruff check tools/cst_book_translator.py tests/tools/test_book_translator.py scripts/build/generate_books_tsv.py` clean.

## Phase 4 — Phase verification
- [ ] Full test run.
  → verify: `uv run pytest tests/tools/test_book_translator.py` exits 0.
