# SPEC — Lookup keys with outer spaces, and one empty key
GitHub issue: https://github.com/digitalpalidictionary/dpd-db/issues/270 (read-only; do not comment or close)
Type: bug (data)

## Overview
42 rows in the `lookup` table have a `lookup_key` with a leading or trailing space. One row has an empty key. The webapp and the KOReader plugin trim the query before the match, so an exact lookup never finds a spaced key. 29 of the 42 have no trimmed twin, so their content is unreachable. 13 have a trimmed twin that lacks the content of the spaced row.

## Current behaviour (verified in the live `dpd.db` and the code)
- Counts: 42 keys where `lookup_key != trim(lookup_key)`, 13 with a trimmed twin, 29 without. 1 key equals `''`.
- 39 of the 42 hold variant notes. `db/variants/variants_modules.py::key_cleaner` keeps spaces (`_CHAR_SET` contains `" "`) and never trims. The multi-word keys come from the extractors in `db/variants/`. All four extractors (`extract_variants_from_cst.py`, `_bjt.py`, `_sya.py`, `_sc.py`) write into one shared dict keyed by `key_cleaner(word)`, then `db/variants/main.py` calls `sync_lookup_column(..., "variant", ...)`.
- 3 of the 42 hold deconstructions: `vinivijjhanaṭṭhenāti `, `akkharappabhedānaṃ `, `ūsakhaṇḍaṃ `. Their source is three lines of `shared_data/deconstructor/manual_corrections.tsv` whose first column has a trailing space. `go_modules/deconstructor/importer/manualCorrections.go` sets `mi.Word = d["compound"]` without a trim, but it does trim `split`. A second reader of the same file, `makeManualCorrections` in `unmatched.go`, also keeps `compound` untrimmed. It builds the set of words removed from the algorithm input. Found in review: with only the first reader trimmed, the trimmed word stayed in the input, a worker produced splits, and `Merge` in `go_modules/deconstructor/data/matchdata.go` let them overwrite the curated split (seen for `vinivijjhanaṭṭhenāti`).
- The empty key `''` holds only `headwords = [54334]` (`yonisomanasikārasutta`). The `sutta_info` row SN46.36 has `sc_code = ''` (the only such row). `tools/sutta_codes.py::make_list_of_sutta_codes` adds `su.sc_code` to its set without a check, and `db/suttas/suttas_to_lookup.py` writes every code as a key.
- `tools/lookup_sync.py::sync_lookup_column` upserts by key and, with `clear_stale=True`, clears or deletes rows no longer in the data. The variant and deconstructor syncs use `clear_stale=True`. The sutta sync uses `clear_stale=False`, but the inflections sync that runs before it clears old non-inflection `headwords` rows (see the note at the top of `suttas_to_lookup.py`).

## What it should do
- `key_cleaner` returns the key trimmed of outer spaces. A spaced key and its trimmed twin then merge in the shared dict with no new merge code.
- `manualCorrections.go` trims `d["compound"]`, the same way it trims `split`. The reader body sits in a helper `matchItemsFromRows` so a test can feed it rows.
- The `mixed` case in the key cleaner fixture file expects trailing spaces (`"dukkha  "`). It encodes the bug and changes to `"dukkha"`.
- `unmatched.go` trims `compound` the same way, in a helper `manualCorrectionWordsFromRows`, so both readers agree.
- `make_list_of_sutta_codes` skips an empty or whitespace-only `sc_code`.
- The next build removes the 42 spaced rows and the empty row through the existing stale-row clearing. Their content is then written under trimmed keys.

## Assumptions & uncertainties
- Verified: all counts and sources above, by SQL and by reading the code.
- Verified in Phase 3: the stale-row clearing removed the spaced rows in a real build. The scripts have no path option, so the build ran on the live database after a backup.
- NOT verified: that no other writer to `lookup` adds spaced keys. The 42 found today all trace to the two sources above. The Phase 3 query on the rebuilt copy confirms this.
- The deconstructor Go step needs the Go toolchain. If the rebuild copy cannot run it, the plan checks the trimmed key in the Go output file instead.

## Constraints
- Do not edit `manual_corrections.tsv`. The Go trim fixes it at read time.
- Do not change the text inside variant notes. Only keys change.
- Never `INSERT OR REPLACE` on `lookup`. No change to `sync_lookup_column`.
- Each touched Python file must pass `ruff check`, `ruff format` and `pyright`. `go vet ./go_modules/...` must pass. Do not run `go build` on a single package path.

## How we'll know it's done
- Tests for the three fixes fail before the fix and pass after.
- On a rebuilt copy of the database, `SELECT count(*) FROM lookup WHERE lookup_key != trim(lookup_key)` returns 0, and `WHERE lookup_key = ''` returns 0.
- On that copy, the 13 trimmed twins keep their headwords and grammar and gain the variant or deconstruction content. The 29 other rows exist under trimmed keys.

## What's not included
- No change to `sync_lookup_column`, the webapp, or the KOReader plugin.
- No edit to the manual corrections file.
- No check that guards future builds against spaced keys. That can be a follow-up if wanted.
