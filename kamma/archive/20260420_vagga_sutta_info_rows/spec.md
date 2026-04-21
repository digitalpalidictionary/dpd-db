# Spec: Render vagga rows for sutta_info.tsv

**GitHub issue:** related work was #192 (vagga sutta codes); confirm if a separate issue number applies.

## Overview
Currently `db/backup_tsv/sutta_info.tsv` holds one row per sutta. This thread extends coverage to **vaggas** by producing TSV rows (same column layout as `sutta_info.tsv`) that represent each vagga. Output lands in a separate preview file under `temp/`; the user merges it into the master document manually.

Scope for this thread: MN, SN, AN, and KN books that already appear in `sutta_info.tsv`. DN has no vaggas in DPD. KN coverage is discovered at runtime — a KN book is included only if vagga headwords exist in dpd-db *and* corresponding sutta rows exist in `sutta_info.tsv`.

The generator is one-shot, throwaway code. It runs once; the output is committed; the code is never reused.

## What it should do

1. Load all vagga headwords from `DpdHeadword` where `lemma_1` matches `/vagga\b/` and `meaning_1` contains a parenthesised `(BOOKCODE...)` range, e.g. `(MN1-10)`, `(SN12.1-10)`, `(AN3.1-10)`, `(UD1)`.
2. Parse the bracketed `dpd_code` from `meaning_1` using the existing `ANY_CODE_RE` in `scripts/add/vagga_codes/shared.py`.
3. Group vagga headwords by their parsed `dpd_code`. Within a group:
   - Choose the headword with the **lowest `id`** as the primary → `dpd_sutta` column (value is `lemma_1` with trailing ` N` homonym suffix stripped).
   - Remaining lemmas (homonym-stripped), joined by `; `, go into `dpd_sutta_var`.
4. Resolve each group's **first sutta** in `sutta_info.tsv`:
   - Parse the range — take the first sutta code (e.g. `MN1-10` → `MN1`; `SN12.1-10` → `SN12.1`).
   - Look up the row in `sutta_info.tsv` whose `dpd_code` matches that first sutta.
5. Emit one TSV row per vagga group, copying **every** column from the first-sutta row as-is, then overwriting:
   - `book`, `book_code` — unchanged (already correct from the sutta row).
   - `dpd_code` — the vagga range (e.g. `MN1-10`).
   - `dpd_sutta` — primary vagga headword lemma.
   - `dpd_sutta_var` — alternate lemmas joined by `; ` (blank if none).
6. Cover the single-vagga samyutta case (`cst_vagga` empty in source) by falling back to `load_section_spans` from `shared.py`, so the vagga row is still emitted.
7. Write output to `scripts/suttas/vaggas/compile_vaggas.tsv` with the same 43-column header as `sutta_info.tsv`. Sort rows in the same order as the corresponding first-sutta rows appear in `sutta_info.tsv` (natural canonical order).

## Assumptions & uncertainties

- **Primary-headword rule:** "lowest id" is a simple, deterministic tiebreaker. The user has not specified the rule; worth confirming during review.
- **Homonym suffix stripping:** lemma like `acelakavagga 1` → `acelakavagga` when emitted in `dpd_sutta`/`dpd_sutta_var`. Matches the convention in existing sutta rows (no trailing counter).
- **Column copy is unconditional ("2A — everything for now"):** sutta-specific fields like `sc_blurb`, `sc_eng_sutta`, `cst_paranum`, `cst_m_page`, `bjt_sutta_code` will be copied from the first sutta verbatim. Refining deferred.
- **Missing `sutta_info.tsv` match:** if a vagga's first sutta code has no row in `sutta_info.tsv`, the vagga is **skipped** and logged to stderr. Expected never to happen for MN/SN/AN; may happen for some KN books — that is the signal that KN book is out of scope.
- **No DB writes.** Output is a TSV file under `temp/` only; the master `sutta_info.tsv` is untouched.
- **KN books in scope (discovered at runtime):** candidates include DHP, UD, ITI, SNP, VV, PV, TH, THI, JA — included only where both vagga headwords and sutta_info rows are present.

## Constraints

- New code goes under `scripts/suttas/vaggas/`.
- Reuse helpers from `scripts/add/vagga_codes/shared.py` (`ANY_CODE_RE`, `DPD_CODE_RE`, `load_section_spans`) where useful.
- No DB writes. No modification to existing `sutta_info.tsv`.
- Follow project rules: modern type hints, `Path` from pathlib, `icecream` for debug, no `sys.path` hacks.
- Throwaway — minimal structure, single runnable entry point.

## How we'll know it's done

- Running `uv run python scripts/suttas/vaggas/compile_vaggas.py` produces `scripts/suttas/vaggas/compile_vaggas.tsv`.
- Running `uv run python scripts/suttas/vaggas/extract_vaggas.py` produces four AN source TSVs (`extract_vaggas_{dpd,cst,sc,bjt}.tsv`) for manual AN1/AN2 alignment.
- Header row exactly matches `sutta_info.tsv` (43 columns, tab-separated).
- Spot-check: MN has 15 vagga rows (three sets of 5), SN has the expected samyutta-vagga count, AN likewise, KN-UD has 8, KN-ITI has 4, etc.
- Every row's `dpd_code` is a parseable range; every `dpd_sutta` is non-empty.
- No duplicate `dpd_code` values in the output.
- User spot-reviews a handful of rows and confirms the column-copy behaviour is acceptable.

## What's not included

- Merging into `sutta_info.tsv` (user does this manually).
- Refining which columns to copy vs blank (deferred).
- Adding other data types (e.g. nipāta, saṃyutta headwords) — vaggas only.
- DN (no vaggas in DPD).
- Any GUI or DB-write path.
- Automated tests — throwaway script.
