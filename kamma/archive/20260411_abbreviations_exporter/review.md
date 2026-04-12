# Review: abbreviations_exporter

- **Date:** 2026-04-12
- **Reviewer:** Claude Sonnet 4.6 (`/kamma:3-review`)
- **Thread:** `20260411_abbreviations_exporter`
- **Issue:** #77
- **Verdict:** PASSED

## Review methods used
- Specification review against `spec.md`
- Plan review against `plan.md` (all phases 1–6 ticked)
- Diff review of all changed files (`git diff --stat` + per-file diff)
- New file review (`help_abbrev_other.jinja`, `abbreviations_other.html`,
  `abbreviations_other_summary.html`, `scripts/find/headwords_matching_abbrev.py`)
- Regression review — verified both webapp rendering blocks place `abbrev_other`
  last and that the DPD `abbrev` pipeline is untouched
- Pattern-mirroring review — template, data-class, and pack/unpack match
  existing `abbrev` / secondary-element patterns

**Not applied:** performance, security, architecture, and lint reviews —
out of scope for a content-export thread. Manual scenario testing was
already done by the user in Phase 5 (`ka`, `AAWG`, `Be`, `SLTP`, `abl`).

## Implementation summary
- `db/models.py` — `abbrev_other` column + `abbrev_other_pack` /
  `abbrev_other_unpack` (`@property`, not `@cached_property`)
- `tools/paths.py` — `abbreviations_other_tsv_path` + two template paths
- `tools/version.py` — `minor` bumped 3 → 4 with comment
- `db/lookup/help_abbrev_add_to_lookup.py` —
  `ensure_abbrev_other_column()` idempotent `ALTER TABLE`, plus
  `add_abbreviations_other()` (remove-then-add, group by abbreviation)
- `exporter/goldendict/data_classes.py` — `AbbrevOtherData` with secondary CSS
- `exporter/goldendict/export_help.py` — `add_abbrev_other_html()` appended
  **last** in `generate_help_html()`
- `exporter/goldendict/templates/help_abbrev_other.jinja` — mirrors
  `help_abbrev.jinja` layout exactly
- `exporter/webapp/data_classes.py` — `AbbreviationsOtherData`
- `exporter/webapp/toolkit.py` — rendering added **last** in both query
  branches; dot-search fix via `or_(ilike(q), ilike(q + "."))`
- `exporter/webapp/templates/abbreviations_other.html` /
  `abbreviations_other_summary.html` — match existing secondary-element
  heading and summary patterns (`other abbreviations: ka` / `ka other abbreviations. ►`)
- `shared_data/help/abbreviations_other.tsv` — source codes capitalized
  (PTS, CPD, Cone, CST, General) by user
- `shared_data/help/abbreviations_other_README.md` — updated counts
  (1089 rows total), rebuild instructions removed

## Findings

### Minor (fixed during review)
1. **Stale docstring** — `db/lookup/help_abbrev_add_to_lookup.py`
   `add_abbreviations_other()` docstring said
   `"""(pts, cone, cpd, general)"""` — lowercase codes were renamed
   by the user to capitalized. **Fixed** → `(PTS, CPD, Cone, CST, General)`.
2. **Stale spec.md source codes** — `spec.md` listed lowercase source codes
   in the Context section and JSON example. **Fixed** → capitalized to
   match the live TSV.

### Residual / out of scope
- `scripts/extractor/compile_abbreviations_other.py` still exists. Plan
  6.1 flags it for deletion; user will remove it manually (not part of
  the exporter pipeline — safe to leave for `/kamma:4-finalize`).
- `scripts/find/headwords_matching_abbrev.py` is a one-off ad-hoc helper
  used by the user to renumber headwords. Untracked in git; user's
  decision whether to keep it.

### No blocking / major findings.

## Verification
- Spec → Implementation: all four sections (DB/Lookup, GoldenDict,
  Webapp, paths.py) satisfied.
- Plan → all phases ticked through Phase 6.
- Patterns: `AbbrevOtherData` mirrors `AbbreviationsData`; template
  mirrors `help_abbrev.jinja`; pack/unpack mirrors other Lookup columns.
- `@property` used (not `@cached_property`) — SQLAlchemy-safe.
- `is_another_value(r, "abbrev_other")` — `lookup_is_another_value.py`
  is column-agnostic, works with the new column.
- `abbrev_other` placed **last** in both webapp rendering branches and
  in the GoldenDict `generate_help_html()` pipeline.
- Dot-search fix scoped to lookup-layer `or_()` — no lookup table data
  duplication, GoldenDict already handles dot-suffix natively.

## Next step
Thread is ready for `/kamma:4-finalize`.
