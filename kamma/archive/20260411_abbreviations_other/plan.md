# Plan: Compile abbreviations from other Pāḷi dictionaries

Issue: #77

This archived plan reflects the implementation that was actually completed for this
thread.

## Phase 1 — Source decisions and reconnaissance
- [x] 1.1 Confirm the output target is `shared_data/help/abbreviations_other.tsv`.
- [x] 1.2 Confirm the implemented source set: `pts`, `dpd_db`, `general`, `cone`, `cpd`.
- [x] 1.3 Confirm Cone abbreviations come from `cone_front_matter.json`.
- [x] 1.4 Confirm CPD abbreviations come from `cpd_clean.db` entry `article_id=90003`.

## Phase 2 — Build the extractor script
- [x] 2.1 Create `scripts/extractor/compile_abbreviations_other.py`.
- [x] 2.2 Implement `AbbrevRow` and category inference helpers.
- [x] 2.3 Implement `load_pts()` from the original
      `shared_data/abbreviations/abbreviations_pts.tsv` source.
- [x] 2.4 Implement `load_dpd_db()` from `dpd.db` where `pos='abbrev'`.
- [x] 2.5 Implement `load_general()` from the original
      `shared_data/abbreviations/abbreviations_bryan.tsv` source.
- [x] 2.6 Implement `load_cone()` from Cone front-matter JSON.
- [x] 2.7 Implement `load_cpd()` from CPD HTML in SQLite.
- [x] 2.8 Implement deterministic dedupe, sort, and TSV writing.
- [x] 2.9 Implement `main()` with per-source count reporting.
- [x] 2.10 Syntax-check the extractor without running the full script automatically.

## Phase 3 — Generate and inspect output
- [x] 3.1 Generate `shared_data/help/abbreviations_other.tsv`.
- [x] 3.2 Confirm header row and stable sorting.
- [x] 3.3 Confirm there are no empty `abbreviation` cells.
- [x] 3.4 Spot-check representative rows including Cone `AAWG`, PTS `A.`, and CPD output.
- [x] 3.5 Record per-source counts in the output/README.

## Phase 4 — Document and clean up
- [x] 4.1 Create `shared_data/help/abbreviations_other_README.md`.
- [x] 4.2 Delete the old `shared_data/abbreviations/` folder after consolidation.
- [x] 4.3 Delete the obsolete `scripts/find/abbreviations_finder.py` helper.
- [x] 4.4 Archive this thread with review notes.

## Notes
- The archived spec and plan were updated after implementation to match the delivered
  source model (`dpd_db` / `general`) rather than the earlier draft model (`dpd` /
  `cst` / `bryan`).
- Deletion of `shared_data/abbreviations/` is intentional final state for this thread;
  references to those files describe source provenance, not files expected to remain.
