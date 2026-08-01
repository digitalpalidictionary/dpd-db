# PTS references from the PTS↔CST concordance into sutta_info

## Overview
Make the authoritative PTS↔CST concordance (Jorge Contreras, CC0; 6,098 entries,
5,232 collated) the SOLE source of PTS page references in `sutta_info`, replacing
the partial PTS coverage currently coming from the Dhamma-Vinaya (DV) Connections
catalogue (only 1,706 / 5,115 rows have a `dv_pts` today).

Source repo: https://github.com/jorgecaa/pts-vri-concordance
Source file: `PTS-CST_Concordance_of_the_Pali_Canon.xlsx`

## What it should do
- Every `sutta_info` row that maps to a collated concordance unit gains a PTS
  reference (e.g. "D i 1,7", "Dhp 21-32") sourced from the concordance.
- The DV catalogue pipeline STOPS supplying PTS: remove `"pts" → "dv_pts"` from
  `get_dv_column_mapping()` in `db/suttas/dv_catalogue_suttas.py`, so
  `update_dv_fields_in_db` no longer overwrites PTS.
- PTS is populated by a NEW step `update_pts_concordance_in_db()`, run AFTER the
  DV step in `db/suttas/suttas_update.py::main()` — mirroring the established
  enrichment pattern.
- The concordance data is vendored as a git-friendly TSV, produced by a converter
  script that reads the source XLSX.
- The PTS display row is moved OUT of the DV catalogue block in both headword
  templates and given its own heading, because it is no longer DV-sourced.

## Measured facts (verified 2026-07-31, not assumptions)
The XLSX was inspected and the join measured against the live `dpd.db` before
planning. These numbers replace the earlier guesses:

- **Sheets:** `About`, `Concordance`, `Summary`. `Concordance` is 6,098 × 14 with
  columns: `Nikāya`, `Work`, `Section`, `Number`, `Title`, `Ee volume`, `Ee page`,
  `PTS reference`, `CST reference`, `Verses`, `Type`, `Status`, `Evidence`, `Notes`.
- **Collated filter:** `Status == "Collated"` → 5,232 rows. Non-collated 866 =
  Jātaka out of scope 548 + no Ee text available 294 (Milindapañha, Nettippakaraṇa,
  Peṭakopadesa) + deest in Ee 14 + section rubric 10 + cross-reference 2.
- **CST reference format:** `s0101m:1-149` — bare file stem, no `romn/` prefix and
  no `.mul.xml` suffix. Normalization rule: `romn/{stem}.mul.xml`.
- **Six CST-ref forms occur among collated entries:** `n` 3,663 · `a-b` 841 ·
  `cN.item` 646 · `cN` 39 · `cN.a-b` 27 · `n.item` 16. The 712 `c`-forms are
  **chapter-relative** numbering (numbering restarts inside a KN chapter) and
  CANNOT be joined by a raw paragraph number — see "What's not included".
- **Join coverage** on `(romn/{stem}.mul.xml, start-paragraph)`, as built by the
  converter: 4,520 numeric-form collated entries collapse to **4,467 distinct keys**
  (39 keys carried 53 surplus entries — see the duplicate-key rule in plan.md), of
  which **3,990 hit a `sutta_info` row, writing 4,384 rows** — 4,476 once the
  range-paranum fallback below is applied, 2.6× today's 1,706.
  338 keys are multi-row (vagga + first sutta).
- **Unmatched breakdown:** 712 chapter-relative forms (not attempted) + 461
  granularity misses (the concordance itemizes what `sutta_info` groups) + 16 keys
  in `romn/s0515m.mul.xml` (Nidd I), a file `sutta_info` does not carry.
- **The AN/SN misses are a granularity mismatch, not a key defect.** The
  concordance itemizes `AN 1.2 … 1.10` at paras 2–10; `sutta_info` groups them as
  one row `AN1.1-10` at para 1. There is no row to write to and never will be.
- **`dpd_code` is a WORSE key, not a fallback:** joining `Nikāya + Number` against
  `dpd_code` matches only 3,095 / 3,737 four-nikāya entries vs the CST join. Do not
  build it.
- **Regression is negligible:** only 2 rows lose their current PTS (`AN3.48`,
  `AN3.63` — the latter has an empty `cst_file`).
- **Range paragraph numbers (found at review, 2026-07-31):** 121 `sutta_info` rows
  store `cst_paranum` as a range (`651-662`). The TSV keys on a bare start
  paragraph, so those rows never join on an exact match; the population step falls
  back to the start of the range, recovering 92 rows — 3 of them template-visible
  (`AN5.257`, `AN5.294`, `AN10.156`). This is a fourth miss category the original
  accounting overlooked.
- **Coverage ceilings:** 7 concordance KN files have no `sutta_info` rows at all
  (`s0510m1`, `s0510m2`, `s0511m`, `s0512m`, `s0515m`, `s0516m`, `s0517m` —
  apadāna/niddesa/paṭisambhidā); conversely `sutta_info` carries 547 Jātaka rows
  the concordance excludes. Neither can be closed here.

## Assumptions & uncertainties
- **Column name:** the existing `dv_pts` column is REUSED, now concordance-sourced.
  The `dv_` prefix becomes a legacy misnomer; a rename to `pts_ref` is a possible
  follow-up but is OUT OF SCOPE here (minimal change).
- **Key ambiguity is real but harmless — do NOT disambiguate.** 338 join keys
  map to more than one `sutta_info` row (`s0101m:1-149` → both `DN1-13` and
  `DN1`; MN1 hits three: `MN1-50`, `MN1-10`, `MN1`). Today's DV data already writes
  PTS to vagga rows, and the templates suppress the PTS row for vagga/saṃyutta rows
  (`is_vagga` / `is_samyutta`), so the write is invisible there. The PTS ref is
  written to **every** row sharing the key. Unit-identity disambiguation was
  considered and rejected as unnecessary complexity.
- **Reference format changes visibly.** DV printed page only (`D i 1`); the
  concordance prints page and line (`D i 1,7`). DECISION: keep the concordance
  string verbatim — the line number is part of what makes this source better. Every
  existing PTS ref will look different after the rebuild.
- **Template placement must change.** The PTS row currently sits INSIDE the DV
  block, under the "Dhamma Vinaya Tools: Sutta Catalogue" heading
  (`exporter/webapp/templates/dpd_headword.html:733`,
  `exporter/goldendict/templates/dpd_headword.jinja:684`). With `dv_pts` removed
  from `dv_exists`, **2,119 rows would render a bare PTS row under no heading**,
  dangling at the end of the BJT section. So the row is moved above the DV block
  and given its own heading. (Both templates keep the surrounding
  `{% if not is_vagga and not is_samyutta %}` gate — vagga/saṃyutta rows still
  display no PTS, as today.)
- **No skip guard at all (revised at review, 2026-07-31).** The step first shipped
  with "run when `table_rebuilt`, otherwise skip", mirroring the DV guard. Review
  showed that to be wrong for exactly the transition this thread creates:
  `table_rebuilt` is False on every incremental run (sheet unchanged + table already
  populated), so `dv_pts` would keep its old DV-format values indefinitely and the
  feature would only land on a full rebuild. The step now runs unconditionally — it
  is local, deterministic and idempotent (~0.3 s over 5,115 rows).
- **No live-DB mutation in this thread:** verification runs on a /tmp copy of
  dpd.db and synthetic test data. The user's real build applies it later.

## Constraints
- Python 3.13, uv, SQLAlchemy, SQLite; `pandas>=2.2.3` + `openpyxl>=3.1.0` already
  installed (pandas Excel engine).
- `sutta_info` is dropped + recreated every rebuild — no migration needed.
- `dv_pts` is a model-only column (NOT in the Google Sheet TSV), populated
  post-rebuild by code.
- Modern type hints, `pathlib.Path`, no `sys.path` hacks; don't mutate ORM objects
  outside the explicit update; use the existing bulk/session update pattern.
- Pre-commit gate: ruff + pyright clean per touched file; repo-wide
  `just typecheck` (pyrefly) clean.
- Git-tracked data file (`pts_concordance.tsv`) must be saved in canonical
  deterministic sort order (by join key) so regeneration is not a full-file reorder.

## How we'll know it's done
- `db/suttas/pts_concordance.tsv` exists, deterministically sorted, joinable.
- `db/suttas/pts_concordance.py::update_pts_concordance_in_db` populates `dv_pts`.
- `db/suttas/suttas_update.py::main` calls it after the DV step.
- DV mapping no longer includes `pts`; `dv_exists` no longer checks `dv_pts`.
- Coverage on a throwaway db copy: 4,476 rows carry a concordance PTS (vs 1,706
  today); the unmatched report classifies misses by cause (chapter-form,
  granularity, no such row) rather than lumping them as failures.
- No dangling PTS row: a row with concordance PTS and no other DV data renders
  under its own heading.
- `uv run pytest tests/db/suttas/` passes; `uv run ruff check` + `uv run pyright`
  per touched file + `just typecheck` all clean.

## What's not included
- **The 712 chapter-relative KN entries** (`file:cN`, `file:cN.item`,
  `file:cN.a-b`). Resolving chapter-relative numbering to CST paragraph numbers
  needs the CST XML chapter structure — a separate piece of work. The converter
  skips them and reports the count. Follow-up.
- Renaming `dv_pts` → `pts_ref` (noted as a follow-up).
- A `dpd_code` fallback join (measured worse; deliberately not built).
- Any attempt to close the granularity gap (concordance per-sutta vs `sutta_info`
  grouped ranges).
- A standalone citation-resolver tool / API.
- Importing non-collated concordance entries (Jātaka, deest, rubric, no-Ee, etc.).
- Changes to the Google Sheet or the DV catalogue itself.
- Running the population against the live dpd.db.
