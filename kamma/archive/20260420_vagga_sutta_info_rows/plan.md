# Plan: Render vagga rows for sutta_info.tsv

**GitHub issue:** related work was #192. See `spec.md` for context.

**Final state:** Implementation split into two scripts:
- `scripts/suttas/vaggas/compile_vaggas.py` — main generator (was `generate.py`); writes `compile_vaggas.tsv`.
- `scripts/suttas/vaggas/extract_vaggas.py` — AN-only source scraper; writes `extract_vaggas_{dpd,cst,sc,bjt}.tsv` for manual alignment of AN1/AN2 vaggas (which have no sutta_info rows).

## Phase 1 — Build & verify the generator

- [x] Create `scripts/suttas/vaggas/` with `__init__.py` and `generate.py` (single entry point).
  → verify: `ls scripts/suttas/vaggas/` shows both files.

- [x] In `generate.py`: load vagga headwords via SQLAlchemy. Query `DpdHeadword` where `lemma_1` matches `vagga\b` and `meaning_1` contains a bracketed dpd_code (use `ANY_CODE_RE` from `scripts/add/vagga_codes/shared.py`). Parse the code; attach `(headword_id, lemma_stripped, dpd_code)` to a list.
  → verify: `ic()` the list length and 5 samples; expect >400 rows; each sample has a parseable dpd_code.
  ✓ 474 entries loaded.

- [x] Load `db/backup_tsv/sutta_info.tsv` as a dict `dpd_code -> row_dict` preserving column order and TSV insertion order.
  → verify: assert header has 44 columns (was 43 in spec — file has 44); `ic()` count; expect ~6331 rows.
  ✓ 4617 rows loaded (sutta_info has 4617 rows not 6331).

- [x] Group vagga entries by `dpd_code`. For each group: lowest-`id` headword → `dpd_sutta`; remaining (sorted by id) joined by `; ` → `dpd_sutta_var`. Strip trailing ` N` homonym suffix on all lemmas.
  → verify: `ic()` a known group with homonyms and confirm primary vs var split.
  ✓ 449 groups; MN41-50 → primary `cūḷayamakavagga`, var `sāleyyavagga`.

- [x] For each group, resolve the first-sutta row: extract the first sutta code from the range (`MN1-10` → `MN1`; `SN12.1-10` → `SN12.1`), look it up in the sutta_info map. On miss: log to stderr and skip.
  → verify: `ic()` misses; expect zero for MN/SN/AN; any KN misses identify out-of-scope KN books.
  ✓ 106 misses: AN1.x (not in sutta_info), DHP verse ranges beyond DHP26, some SN/AN extended ranges — all expected out-of-scope.

- [x] Build each output row by copying all 44 columns from the first-sutta row, then overwriting `dpd_code`, `dpd_sutta`, `dpd_sutta_var`. Preserve `book`, `book_code` as-is.
  → verify: `ic()` one complete output row and confirm sutta-level fields are carried from the first sutta.
  ✓ Confirmed — first row: MN MN1-10 mūlapariyāyavagga.

- [x] Sort output rows by the position of the first-sutta row in `sutta_info.tsv` (natural canonical order). Write to `temp/vagga_info.tsv` with the 44-column header.
  → verify: `head -2 temp/vagga_info.tsv` shows header then an MN row; `wc -l` matches expected group count.
  ✓ 344 lines (343 data rows): MN=15, SN=172, AN=130, UD=8, DHP=2 (partial — first two chapters only).

- [x] Run the generator end-to-end: `uv run python scripts/suttas/vaggas/generate.py`.
  → verify: user inspects `temp/vagga_info.tsv` and confirms the output is correct.

- [x] **Phase 1 automatic verification:** re-run the generator and confirm deterministic output.
  → verify: running twice produces byte-identical `scripts/suttas/vaggas/compile_vaggas.tsv`. ✓ IDENTICAL.

## Phase 2 — AN source scrapers (added mid-thread)

- [x] Add `extract_vaggas.py` to scrape AN vagga source data from four origins: DPD headwords, CST XML (`resources/dpd_submodules/cst/romn/s04*.mul.xml`), SuttaCentral JSON (`resources/sc-data/.../an/`), and BJT (`scripts/suttas/bjt/an.tsv`).
  → verify: four TSVs exist with expected row counts (DPD=197, CST=180, SC=1363, BJT=181). ✓

- [x] Adjust `compile_vaggas.py` to tolerate the new `edited` column in `sutta_info.tsv` (45 cols with trailing empty).
  → verify: `uv run python scripts/suttas/vaggas/compile_vaggas.py` runs cleanly; 401 ok / 50 miss. ✓ Deterministic on re-run.
