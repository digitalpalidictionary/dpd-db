# Spec: stray hyphen in the book code of range sutta codes

**GitHub issue:** https://github.com/digitalpalidictionary/dpd-db/issues/208 (the user posts on GitHub, not the agent)
**Handoff brief:** /home/bodhirasa/OpenBot/Shared/handoff-dpd-db-208.md
**Repo:** /home/bodhirasa/MyFiles/3_Active/dpd-db

## Overview
`SuttaInfo.sc_book_code` (db/models.py:832) is `re.sub(r"\d+\.*-*\d*", "", self.sc_code)`.
For a range code it leaves a hyphen. `AN2.1-10` gives `AN-`. `SN39.1-15` gives `SN-`.
`tbw` and `tbw_legacy` build their URL from this value, so they give `.../sn-/sn39.1-15.html`.

## What it should do
- `sc_book_code` returns only the leading letters of `sc_code`. `AN2.1-10` gives `AN`.
- Change line 834 to `re.sub(r"\d.*", "", self.sc_code)`.
- Remove the workaround in `s_4nt_link` (db/models.py ~lines 927-928): the comment
  `# sc_book_code leaves a trailing hyphen on range codes (SN39.1-15 → "SN-")` and the `.rstrip("-")`
  call. Use `sc_book_code.lower()` directly. The workaround exists only for this bug. The user approved
  this wider scope on 2026-10-27.
- Codes that work now stay the same: `AN3.1`, `MN1`, `DHP1-20`, `DHP90-00`, `ITI1`, `UD1.1`, `SNP1.1`, `THAG1.1`.

## Verified facts (2026-10-27)
- 5,115 rows in `sutta_info` have an `sc_code`. 215 of them change: 136 `SN-` become `SN`, 79 `AN-` become `AN`.
  (Probe over every real row in dpd.db.)
- 26 DHP range rows (`DHP1-20`) already give `DHP`. They do not change.
- No row has an `sc_code` that is not letters followed by a digit (0 rows).
- Only db/models.py uses `sc_book_code` or this regex. (`rg --hidden`, excluding archive and graphify-out.)
- Other callers inside db/models.py: `sc_vagga_link`, `tbw`, `tbw_legacy`, `s_4nt_link`.
- `s_4nt_link` output changes on 0 rows with the regex fix alone.
- `sc_vagga_link` changes on 4 rows, all saṃyutta rows (SN39, SN49, SN50, SN53). Before:
  `https://suttacentral.net/sn--samandakavagga`. After:
  `https://suttacentral.net/pitaka/sutta/linked/sn/sn-salayatanavaggasamyutta/sn39`. The old link was wrong,
  so this is a side fix.

## Assumptions and unverified
- UNVERIFIED: whether thebuddhaswords.net hosts range pages. The brief reports 404 for
  `/an/an2.1-10.html` and 509 for single pages on 2026-10-27. Do not claim the links work after the fix.
- The 4 new `sc_vagga_link` URLs were checked as strings only. Nobody opened them.

## Constraints
- No git, no commit, no push, no GitHub posts. No edits to `.env` or `.ini`.
- Comments only for WHY. Match the surrounding code style.

## How we'll know it's done
- The new tests fail before the fix and pass after it.
- `uv run pytest tests/db` passes. Ruff and pyright pass on the touched files.
- The probe over all rows shows exactly 215 changed `sc_book_code`, 215 `tbw`, 215 `tbw_legacy`,
  4 `sc_vagga_link`, and 0 `s_4nt_link`. This also holds after the workaround is removed.
- Reverting the regex fix makes the new tests fail. Restoring it makes them pass.

## What's not included
- No change to `dhamma_gift` (it already works).
- No live check of Buddha's Words pages.
