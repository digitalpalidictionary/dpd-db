## Thread
- **ID:** 20260510_nikaya_tikas
- **Objective:** Wire up the four nikāya ṭīkās (`dnt`, `mnt`, `snt`, `ant`) into `cst_source_sutta_example.py`, fold the DN abhinavaṭīkā into `dnt` with a distinct `DNnt` source label, add the `DNnt` abbreviation, and surface the four codes in the gui2 book dropdown.
- **GitHub issue:** #150 (left open per user instruction).

## Files Changed
- `tools/cst_source_sutta_example.py` — added `dnt_digha_nikaya_tika`, `mnt_majjhima_nikaya_tika`, `snt_samyutta_nikaya_tika`, `ant_anguttara_nikaya_tika` parsers + four dispatcher cases.
- `shared_data/help/abbreviations.tsv` — new row `DNnt = Dīgha Nikāya Nava-ṭīkā, Sādhuvilāsinī` between `DNa` and `DNt`.
- `gui2/dpd_fields_examples.py` — four new entries in `book_codes` (DNt, MNt, SNt, ANt), placed after all commentaries and before VISMa.
- `kamma/threads/20260510_nikaya_tikas/{spec,plan,review}.md` — thread artifacts.

## Findings
No findings.

- Spec coverage: every requirement met. `dnt` returns mixed `DNt…` / `DNnt…` results in one call; `mnt`/`snt`/`ant` each return their own prefix. Verified by user in gui2.
- Plan completion: all phases done. Phase 5 was added mid-thread for the abbreviation row and renumbered 5/6.
- Architecture decisions held: parsers mirror the corresponding `dna/mna/sna/ana` commentary functions; abhinava detection uses a lazy `g.is_abhinava` free attribute, matching the existing `g.is_bhikkhuni` pattern.
- Pre-existing mis-attribution in `DNt` row of `abbreviations.tsv` (says "Sādhuvilāsinī" but that work is the abhinavaṭīkā = `DNnt`) was flagged to user but **not fixed** in this thread — out of scope.
- No regressions: existing book codes left byte-identical except for new dispatcher cases inserted alongside their commentary siblings.

## Fixes Applied
- Switched abhinava prefix from `DNAt` → `DNnt` mid-implementation to (a) align with CPD's `n`-for-nava convention and (b) avoid a numeric collision (`DNt` + 2 vs `DNt2` + N).

## Test Evidence
- `uv run ruff check tools/cst_source_sutta_example.py gui2/dpd_fields_examples.py` → all checks passed.
- Manual smoke test from CLI: `dnt` + brahmajāl → 59 examples (29 `DNt…`, 30 `DNnt…`); `mnt` + mūlapariyāy → 34; `snt` + paṭiccasamuppād → 58; `ant` + rūpādivagg → 2. No exceptions.
- User confirmed manual test in gui2 working.

## Verdict
PASSED
- Review date: 2026-05-10
- Reviewer: kamma (inline)
