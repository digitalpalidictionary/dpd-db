# Sutta Name Aliasing

## Overview
Allow multiple sutta names (canonical CST, SC, BJT) to resolve to the same `SuttaInfo`
row and render the same sutta tab. Achieved by populating `SuttaInfo.dpd_sutta_var`
with curated alias names (one per `;`-separated value) and replacing the
`lemma_1`-only resolver with a multi-name resolver.

Branch: `feature/sutta-aliases` (breaking changes, must not land on `main` directly).

## Why
Users searching by SC or BJT names currently get nothing for sutta info. Variant
names already exist as headwords in `dpd_headwords`; they should fire the sutta tab
and surface the canonical sutta data.

## Repo context
- `db/models.py:848` — `lemma_1` declares `ForeignKey("sutta_info.dpd_sutta")`.
  SQLite does not enforce FKs by default; variant headwords already exist with
  `lemma_1` values that don't match any `dpd_sutta`, so the FK is documentation
  only. No FK removal needed.
- `db/models.py:948` — `su: Mapped[SuttaInfo] = relationship()`. No eager-loading
  call sites (`grep` clean). Safe to convert to `cached_property`.
- `db/models.py:1353` — `needs_sutta_info_button` reads
  `lemma_1 in sutta_info_set`.
- `tools/cache_load.py:14` — `load_sutta_info_set()` queries
  `(dpd_sutta, dpd_sutta_var)` but currently includes only `dpd_sutta`. The
  `dpd_sutta_var` line is commented out with the note "exclude for now".
- `db/models.py:757` — `sutta_info_count` already does
  `or_(dpd_sutta, dpd_sutta_var)` but is single-value only.
- `db/suttas/suttas_update.py` — downloads sutta_info TSV from a Google Sheet,
  drops and recreates `SuttaInfo`. The sheet is the source of truth.
- Templates and exporters consume `i.su.<field>` — they don't care how `su` resolves.

## Workflow (curation-first)
The Google Sheet is the only stable source of truth. The local TSV at
`db/backup_tsv/sutta_info.tsv` is a working copy that gets overwritten on every
download.

1. User runs `db/suttas/suttas_update.py` (downloads fresh sheet to the local
   TSV, populates `SuttaInfo`).
2. User runs a one-off **candidate-finder** script that reads `SuttaInfo`
   (already populated from the latest sheet — no re-download needed), computes
   cleaned `sc_sutta` and `bjt_sutta` candidates, validates them, and writes
   ALL candidates with status to `temp/sutta_alias_candidates.tsv`.
3. User reviews the candidates TSV, copies approved aliases into the Google
   Sheet's `dpd_sutta_var` column (`;`-separated).
4. User re-runs `suttas_update.py` to pull the curated values back into the DB.
5. Resolver code (changed in this thread) picks up the new aliases automatically.

The candidate-finder is **never** wired into the build pipeline. It's a manual
tool. Its output file (`temp/sutta_alias_candidates.tsv`) is gitignored / safe
to overwrite — the sheet is the durable home for curated aliases.

## What it should do
1. **Candidate-finder script:** for each `SuttaInfo` row, propose cleaned alias
   names from `sc_sutta` and `bjt_sutta`, validate against existing headwords
   and existing aliases, and emit `temp/sutta_alias_candidates.tsv` with one
   row per candidate including status. The user reviews this file and manually
   copies approved aliases into the Google Sheet.
2. **Resolver:** `DpdHeadword.su` resolves to the canonical SuttaInfo whether
   `lemma_1` matches `dpd_sutta` directly or appears in any row's
   `dpd_sutta_var` (`;`-separated).
3. **Button:** `needs_sutta_info_button` returns true for variant headwords too.
4. **Sutta tab:** renders identical content for canonical and variant headwords.

## Cleaning rules
- `sc_sutta`: strip a single trailing `ṃ`.
- `bjt_sutta`: strip leading `^\d+\.\s*` then strip a single trailing `ṃ`.
- Both: trim whitespace; drop if empty or equal to `dpd_sutta`.

## Validation rules (candidate-finder)
For each candidate alias, output one of these statuses in the TSV:
- `ok` — exists as a headword, no collision; safe to add.
- `missing_headword` — cleaned name not found as `DpdHeadword.lemma_1`.
- `collides_with_dpd_sutta` — equals `dpd_sutta` of a different SuttaInfo row.
- `collides_with_existing_alias` — already present in another row's
  `dpd_sutta_var`.
- `duplicate_in_row` — sc and bjt cleaned to the same value (emit once).

Candidates TSV columns:
`dpd_sutta | source (sc|bjt) | raw | cleaned | status | note`.

## Storage format
`dpd_sutta_var` is a `;`-separated string (multi-value). No schema change
(column is already `str`). Empty when no aliases.

## How we know it's done
- `tools/sutta_name_cleaning` unit tests pass.
- Candidate-finder runs against the current DB and produces a non-empty TSV with
  the documented columns and statuses.
- Resolver: a Python REPL check shows that a headword whose `lemma_1` matches a
  manually-added test alias resolves to the canonical SuttaInfo via `i.su` and
  has `i.needs_sutta_info_button == True`.
- Webapp spot-check (USER): visit a known variant headword, confirm the sutta
  tab renders with canonical content.
- Existing test suite passes: `uv run pytest tests/`.

## Out of scope
- Removing the FK declaration on `lemma_1`.
- Pushing aliases back to the Google Sheet (user does this manually after review).
- Re-downloading the sheet inside the candidate-finder (it reads from the
  already-populated `SuttaInfo` table).
- Modifying `db/backup_tsv/sutta_info.tsv` directly (it gets overwritten on
  every download, so it is not a safe place to persist curated data).
- Including `cst_sutta`, `dpr_code`, or other sources.
- Making aliases searchable via Lookup (variant headwords are already searchable
  via their own inflections).
- Auto-population of `dpd_sutta_var` in the build pipeline.
- Any changes to templates or exporters.

## Assumptions / uncertainties
- Assumes no joinedload/selectinload on `.su` (verified by grep).
- Cleaning rules may miss edge cases (multi-word names with internal `ṃ`,
  trailing punctuation). The TSV review is the safety net.
- Assumes `sc_sutta` and `bjt_sutta` values in the sheet are reasonably clean
  (no stray HTML, no duplicate spaces). Will normalise whitespace defensively.
- Aliases match **exact** headword `lemma_1` values (e.g. "mettā 1"), not bare
  word forms ("mettā"). A non-sutta headword cannot accidentally collide with
  an alias because `lemma_1` includes the disambiguating number. No `pos` check
  needed.
