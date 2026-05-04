# Spec: AN vagga per-source extractors

**GitHub issue:** [#236 — Sutta Table: Add AN subsections](https://github.com/digitalpalidictionary/dpd-db/issues/236)
(parent: "Sutta table: Add all missing subsections, vagga and sutta")

## Overview
Issue #236 covers three AN subsection levels: nipāta, paṇṇāsaka, vagga. **This thread covers
vaggas only** — the most numerous level. Nipātas (11 rows) and paṇṇāsakas come later.

The previous attempt produced `scripts/suttas/vaggas/extract_vaggas.py` (a single
multi-source script writing into `scripts/suttas/vaggas/extract_vaggas_*.tsv`) plus
`compile_vaggas.py` that tried to merge those into `sutta_info.tsv` rows. The compile
step misfired. The user wants to discard the centralised approach and instead extract
vagga rows per source in the per-source script folders, then manually align afterwards.

## What it should do
Produce one TSV per source containing one row per AN vagga, located alongside the
existing per-source `an.py` scripts:

| Source | Script                              | Output TSV                          |
| ------ | ----------------------------------- | ----------------------------------- |
| DPD    | `scripts/suttas/dpd/an_vaggas.py`   | `scripts/suttas/dpd/an_vaggas.tsv`  |
| CST    | `scripts/suttas/cst/an_vaggas.py`   | `scripts/suttas/cst/an_vaggas.tsv`  |
| SC     | `scripts/suttas/sc/an_vaggas.py`    | `scripts/suttas/sc/an_vaggas.tsv`   |
| BJT    | `scripts/suttas/bjt/an_vaggas.py`   | `scripts/suttas/bjt/an_vaggas.tsv`  |

Each script is independently runnable as `__main__`. Logic is adapted from the
working extractors already in `scripts/suttas/vaggas/extract_vaggas.py`.

## Column conventions per source
Columns mirror the `sutta_info.tsv` naming for the relevant source. Columns the source
cannot fill (e.g. `dpd_code` from CST/SC/BJT) stay empty for the user to fill manually.

- **DPD** — `book`, `book_code`, `dpd_code`, `dpd_sutta`, `dpd_sutta_var`, `id`, `lemma_1`,
  `family_set`, `meaning_1`, `meaning_lit`, `meaning_2`, `notes`
- **CST** — `book`, `book_code`, `dpd_code`, `cst_code`, `cst_nikaya`, `cst_book`,
  `cst_section`, `cst_vagga`, `cst_sutta`, `cst_paranum`, `cst_m_page`, `cst_v_page`,
  `cst_p_page`, `cst_t_page`, `cst_file`
- **SC** — `book`, `book_code`, `dpd_code`, `sc_code`, `sc_book`, `sc_vagga`, `sc_sutta`,
  `sc_eng_sutta`, `sc_blurb`, `sc_card_link`, `sc_pali_link`, `sc_eng_link`, `sc_file_path`
- **BJT** — `book`, `book_code`, `dpd_code`, `bjt_sutta_code`, `bjt_web_code`,
  `bjt_filename`, `bjt_book_id`, `bjt_page_num`, `bjt_page_offset`, `bjt_piṭaka`,
  `bjt_nikāya`, `bjt_major_section`, `bjt_book`, `bjt_minor_section`, `bjt_vagga`,
  `bjt_sutta`

## Assumptions & uncertainties
- The vagga extraction logic in the existing `extract_vaggas.py` is correct and current
  (it produces 198 DPD rows, 181 CST rows, 1364 SC rows, 182 BJT rows). We preserve
  behaviour. If a source TSV row count or content changes, the user will flag during testing.
- DPD source: read straight from the database via `DpdHeadword`, filtering on
  Aṅguttara-Nikāya `meaning_2` plus `family_set`/`meaning_1` heuristics. Same logic as
  current `export_dpd()`.
- CST source: parse the 11 AN XML files in `resources/dpd_submodules/cst/romn/`,
  grouping `<head rend="chapter">` (vagga) blocks and capturing the first numbered
  sub-entry as the anchor sutta + paranum, plus current pb-page state. Same logic as
  current `export_cst()`.
- SC source: read `resources/sc-data/.../sutta/an/`, group by `(book, vagga)` to
  produce one row per vagga. Special-case `an1`/`an2` as in current code. Same logic as
  current `export_sc()`.
- BJT source: read existing `scripts/suttas/bjt/an.tsv` (already produced by `bjt/an.py`)
  and collapse to one row per `(book, minor_section, vagga)` group. Same logic as
  current `export_bjt()`.
- We do **not** delete `scripts/suttas/vaggas/extract_vaggas.py` or `compile_vaggas.py`
  in this thread (the user said work only in the per-source folders). They may be
  cleaned up later; for now they coexist. No new logic depends on them.

## Constraints
- One TSV per source. No combined output, no merge step.
- Script run from project root: `uv run python -m scripts.suttas.<src>.an_vaggas`.
- No new dependencies. Reuse the libraries already used by the per-source `an.py`.
- Modern Python type hints, `Path` for paths, `printer as pr` for output. No `print()`.
- Do not modify the database, `sutta_info.tsv`, or any other source-of-truth file.
- Do not run scripts unless explicitly asked — user runs them.

## How we'll know it's done
- Each script runs to completion when invoked by the user and writes a non-empty TSV
  with the columns listed above.
- Row counts approximately match the existing centralised extractor:
  DPD ≈ 197, CST ≈ 180, SC ≈ 1363 (data rows excluding header), BJT ≈ 181.
  Anything significantly off → flag.
- User spot-checks the TSVs and confirms.

## What's not included
- AN nipātas (11 rows) and paṇṇāsakas — separate future thread.
- DN/MN/SN/KN vagga extraction.
- Any merge/compile step into `sutta_info.tsv`.
- Any change to the database schema or `sutta_info.tsv` directly.
- Any cleanup of `scripts/suttas/vaggas/`.
