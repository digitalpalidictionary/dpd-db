# Plan — vagga sutta codes

## Phase 1 — Scaffolding & shared helpers
- [ ] Create package `scripts/add/vagga_codes/` with `__init__.py`.
- [ ] `shared.py`:
  - [ ] `load_vagga_ranges()` → dict `{(book_code, inner_or_None, chapter_num): (first_dpd_code, last_dpd_code, cst_vagga_name)}` from `db/backup_tsv/sutta_info.tsv`.
  - [ ] `format_range(book_code, first_code, last_code)` → `"MN1-10"` / `"SN1.1-10"` / `"AN3.1-10"`.
  - [ ] `parse_chapter(meaning_1)` → `int | None` (regex `(?:Chapter|Section)\s+(\d+)`).
  - [ ] `strip_trailing_code(text)` → remove trailing ` (<book><digits>(.digits)?(-digits)?)` if present.
  - [x] `chapter_to_vagga(text)` — case-preserving word-bounded replacement of `chapter(s)` → `section(s)`.
  - [x] `write_preview_tsv(path, rows)` — cols `id, lemma_1, old_family_set, new_family_set, old_meaning_1, new_meaning_1, status`; rows sorted by natural sort on `new_meaning_1`.
  - → verify: `uv run python -c "from scripts.add.vagga_codes.shared import load_vagga_ranges; d=load_vagga_ranges(); print(len(d), d[('MN',None,1)])"` prints non-zero and a tuple starting with `MN1`.
- [ ] `runner.py` CLI: `python -m scripts.add.vagga_codes.runner --book MN|SN|AN|DHP|...` + `--all`. Dispatches to per-book module's `process()` function. Hard guard: grep for `.commit(` in package → must be empty.
  - → verify: `--help` shows book choices; running without `--book` prints usage.

## Phase 2 — Per-book modules (iterate with user)
Each module exposes `process(session, runs) -> list[dict]` returning preview rows; runner writes TSV.
Every module applies `chapter_to_vagga(...)` to both `family_set` and `meaning_1`.
MN additionally normalizes `family_set` `"chapters of the Majjhima Nikāya"` → `"vaggas of the Majjhima Nikāya"`.

- [x] `mn.py` — 15 vaggas. `family_set` = `"vaggas of the Majjhima Nikāya"`. No inner section.
  - → verified: 26 rows, 25 replaced + 1 `no-chapter` (devadahonupada refs two vaggas).
- [x] User reviewed MN TSV; applied 25 updates via `apply.py` (committed). Leftover `devadahonupada` fixed manually by user — MN fully done.
- [x] `sn.py` — ~200 vaggas across 52+ saṃyuttas. Inner section from `family_set` trailing int. Chapter lookup is by CST vagga number (not position) so peyyāla vaggas like `5. Oghavaggo` after gap `[1, 3, 4, 5]` resolve correctly. Single-vagga samyuttas fall back to `load_section_spans()`.
  - → verified: `naḷavagga` → `SN1.1-10`; `oghavagga 06` → `SN49.45-54`.
- SN known leftovers (user to revisit):
  - 10 `chapter-N-not-in-cst` — e.g. SN45 chapters 9-15 and SN49 chapter 2 appear in DPD but are missing from TSV's `cst_vagga`; likely "peyyāla" / repeat vaggas under Mahāvagga. Either add rows to the Google sheet or hard-code.
  - 3 `no-chapter` — `punāppamādavagga`, `sabbāniccavagga` (empty meaning_1), `gativagga` (`meaning_1` already has `SN56.102-131 Pañcagatipeyyālavagga` in free-text).
  - 1 `bad-family-set` — `gāmaṇivagga` (id 24770): no family_set, `meaning_2` already holds `SN42.1-13`.
- [x] `an.py` — 209 headwords. Chapter + nipāta name parsed from `meaning_2`
  (AN's pattern: `meaning_1` is empty, descriptor lives in `meaning_2`).
  Position-based run lookup within each `(AN, nipata)`, with fallback to
  range embedded in `meaning_2` (`Aṅguttara Nikāya N.first-last`) for AN1/AN2
  where the TSV has no/partial `cst_vagga`. Writes a fresh `meaning_1`
  of the form `Vagga N of {NipātaName} (AN{code})`.
  - → verified: 206/209 rewritten.
- AN known leftovers (3 rows — DPD data issues, not code issues):
  - 13285 `āhuneyyavagga 1` — `family_set` says "AN 1" but `meaning_2` places it in Chakkanipāta (AN6).
  - 72413 `nissāyavagga` — `family_set` says "AN 1" but `meaning_2` places it in Ekādasakanipāta (AN11).
  - 17857 `etadaggavagga 1` — `meaning_2` is free-text "Chapter on 'This is the Number One'" with no chapter number.
- [x] `kn.py::_process_dhp` — 26 vaggas of the Dhammapada. Applied via `apply.py` (26 updates committed).
- [x] `kn.py::_process_simple("UD", …)` — 11 vaggas of Udāna. Applied via `apply.py` (11 updates committed).
- [ ] `iti.py` — 1 vagga of Itivuttaka.
- [x] `kn.py::_process_simple("SNP", …)` — 6 vaggas of Sutta Nipāta. Applied via `apply.py` (6 updates committed).
- [x] `kn.py::_process_simple("PV", …)` — 4 vaggas of Petavatthu. Applied via `apply.py` (4 updates committed).
- [x] `kn.py::_process_simple("VV", …)` — 7 vaggas of Vimānavatthu. Applied via `apply.py` (7 updates committed).
- [ ] `th.py` / `thi.py` / `ja.py` — only if DPD headwords exist; generate TSV or document absence.

## Phase 3 — Consolidated preview
- [ ] `runner.py --all`: run every registered book, write each TSV, then merge to `temp/vagga_codes_all.tsv` with leading `book` column.
- [ ] Print per-book summary: matched / replaced / appended / unmatched counts.
- [ ] Print global unmatched list with enough context (id, lemma_1, family_set, meaning_1) for manual fixes.
  - → verify: merged file's row count = sum of per-book counts; no duplicate ids.

## Non-negotiables
- No `.commit(` anywhere in the package.
- No schema changes.
- Each book's quirks isolated to its own module.
