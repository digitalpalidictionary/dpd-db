# Spec — Add sutta-code ranges to vagga headwords

## Overview
Enrich `meaning_1` of every vagga headword in DPD with a sutta-code range
(e.g. `(SN1.1-10)`, `(MN1-10)`, `(AN3.1-10)`), and globally replace the word
`chapter`/`chapters` (any case) with `vagga`/`vaggas` in both
`family_set` and `meaning_1`. No DB writes in this thread — output is per-book
TSV previews that the user reviews and refines iteratively.

## What it should do
- For each `DpdHeadword` whose `family_set` starts with `"vaggas of"`, compute
  the vagga's sutta-code range by joining against `db/backup_tsv/sutta_info.tsv`.
- Join key: `(book_code, inner_vagga, chapter_number)` where
  - `book_code` + `inner_vagga` come from `family_set`
    (e.g. `"vaggas of the Saṃyutta Nikāya 22"` → `SN`, `22`).
  - `chapter_number` comes from `meaning_1` via `r"(?:Chapter|Vagga)\s+(\d+)"`.
  - CST vagga name (`"N. Xxxvaggo"`) in the TSV yields the same N.
- Apply `Chapter`/`chapter`/`Chapters`/`chapters` → `Vagga`/`vagga`/
  `Vaggas`/`vaggas` to both `family_set` and `meaning_1` (case-preserving,
  word-bounded). Computed chapter number is parsed from the *original*
  `meaning_1` before substitution, so nothing breaks.
- Output per-book TSV to `temp/vagga_codes_<BOOK>.tsv` with columns:
  `id, lemma_1, old_family_set, new_family_set, old_meaning_1, new_meaning_1, status`.
- Rows sorted by a natural sort on `new_meaning_1` (numeric-aware), so entries
  appear in sutta-code order and `"in reference to …"` rows collect at the end.
- Merged output `temp/vagga_codes_all.tsv` once all books processed.
- **No `session.commit()` anywhere.** Apply step is a separate future thread.

## Repo context
- `db/models.py` — `DpdHeadword` model. `family_set`, `meaning_1`, `meaning_2`,
  `lemma_1` are the relevant columns.
- `db/db_helpers.get_db_session(Path('dpd.db'))` — standard session factory.
- `db/backup_tsv/sutta_info.tsv` — 6,332 rows. Columns include `book_code`,
  `dpd_code`, `cst_vagga`. `cst_vagga` string begins with `"N. "`.
- 458 vagga headwords total; distribution: AN ≈ 200, SN ≈ 200, Dhp 26, MN 15,
  Ud 11, Sn 6, Vv 7, Pv 4, Iti 1, plus Th/Thi/Ja entries in TSV that may or
  may not have DPD headwords.
- Existing `meaning_1` examples:
  - `"Chapter 1 of the Devatāsaṃyuttaṃ, Book 1 of the Saṃyutta Nikāya (SN1.1)"`
  - `"Chapter 5 of Dasakanipāta, Aṅguttara Nikāya 10.41-50"` (code is in
    `meaning_2` in many AN rows, not `meaning_1` — needs checking per book)
- Format rules:
  - MN: `MN1-10` (no inner vagga)
  - SN/AN: `SN1.1-10`, `AN3.1-10`
  - Dhp/Ud/Iti/Sn/Pv/Vv: derived from `dpd_code` structure in TSV

## Assumptions & uncertainties
- `Chapter N` / `Vagga N` in `meaning_1` is consistent for SN/AN (confirmed
  on SN1 sample). Other books may differ — per-book module handles its own quirks.
- `family_set` trailing integer = inner vagga (SN, AN). Other books have no
  trailing integer and map to `book_code` alone.
- Duplicate vagga names across saṃyuttas (e.g. `Paṭhamavaggo`) are handled by
  keying on inner vagga, not name.
- Homonyms like `jarāvagga 1`, `acelakavagga 2` — the digit is a DPD
  disambiguator, not the chapter. Use `meaning_1`'s `Chapter N`, not `lemma_1`.
- Some rows already have `(SN1.x)` appended — new run must replace a trailing
  `(<sutta-code>)` cleanly, preserve other parenthetical content.
- Th / Thi / Ja / others: generate preview anyway, flag for user decision.

## Constraints
- Only touch vagga headwords (`family_set LIKE 'vaggas of%'`).
- No DB writes, no migrations, no schema changes.
- Per-book modules so each book's wording quirks are isolated.
- Iterate one book at a time; user reviews each TSV before moving on.

## How we'll know it's done
- `temp/vagga_codes_<BOOK>.tsv` exists for every book the user wants covered.
- User has reviewed each TSV and confirmed the `new_meaning_1` is correct.
- Unmatched rows listed clearly per book.
- `temp/vagga_codes_all.tsv` merges everything for final review.

## Out of scope
- Writing to the database.
- Parsing CST XML (TSV already has what we need).
- Editing `meaning_2`, `sc_vagga`, or non-vagga headwords.
- Building the apply-to-DB script (future thread once previews are approved).
