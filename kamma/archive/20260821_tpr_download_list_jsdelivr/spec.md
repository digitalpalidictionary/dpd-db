# Spec: fix TPR download-list updater for jsdelivr mirror + new download_list_2.json

## Overview
The upstream `tpr_downloads` submodule (bksubhuti's repo, feeds the Tipitaka Pali
Reader app's in-app download catalog) is migrating away from
`https://github.com/bksubhuti/tpr_downloads/raw/master/...` links to
`https://cdn.jsdelivr.net/gh/bksubhuti/tpr_downloads@master/...` links, because
GitHub raw downloads are blocked in Myanmar while the jsdelivr CDN mirror is not.
As part of that migration he added a second catalog file,
`download_source_files/download_list_2.json`, which the *new* TPR app version reads;
older TPR versions still read the original `download_source_files/download_list.json`.
He confirmed both files need to stay populated during the transition.

Our exporter (`exporter/tpr/tpr_exporter.py::copy_zip_to_tpr_downloads`) writes DPD's
own release/beta entry into that catalog every time we run the TPR export. It
currently has two problems that this thread fixes:

1. It hardcodes a GitHub raw URL for our own `dpd.zip`/`dpd_beta.zip` entries —
   exactly the link format being retired.
2. It locates "the DPD entry" and "the DPD beta entry" by a **hardcoded array
   index** (`download_list[12]`, `download_list[33]`) into `download_list.json`.
   Upstream already reordered/trimmed that list once (5 entries removed), which
   would silently make our script overwrite the wrong, unrelated entry.
3. It only knows about `download_list.json` — it has no path for the new
   `download_list_2.json`, so that file never gets DPD's release info at all.

## What it should do
- Generate the jsdelivr CDN URL (`https://cdn.jsdelivr.net/gh/bksubhuti/tpr_downloads@master/release_zips/<file>.zip`)
  instead of the GitHub raw URL, for both the release and beta entries.
- Locate the DPD release entry and DPD beta entry in a download-list JSON by a
  **stable key** instead of array index: match on the tail of the existing `url`
  field — `.../release_zips/dpd.zip` for the release entry, `.../release_zips/dpd_beta.zip`
  for the beta entry. This is stable across CDN-vs-raw domain changes and across
  upstream reordering, because it's the actual filename we control, not upstream's
  list position.
- Apply the same update to **both** `download_source_files/download_list.json` and
  `download_source_files/download_list_2.json`. Each file is handled independently:
  if one is missing (e.g. `download_list_2.json` isn't present in the currently
  checked-out submodule commit) or a target entry isn't found in it, log a warning
  via `pr` and skip that file rather than crashing the whole TPR export pipeline.
- Add `tpr_download_list_2_path` to `tools/paths.py` alongside the existing
  `tpr_download_list_path`.

## Assumptions & uncertainties
- **Verified:** current `download_source_files/download_list.json` (submodule at
  `04c745d`) has the release entry at index 12 (`"DPD July 2026 release"`, category
  `"Dictionaries"`, url ending `release_zips/dpd.zip`) and the beta entry at index 33
  (`"DPD Beta"`, category `"Other Beta"`, url ending `release_zips/dpd_beta.zip`) —
  these are the two entries the existing hardcoded-index code touches today.
- **Verified:** upstream `origin/master` (not yet pulled into our submodule
  checkout) already removed 5 entries ahead of index 12 in `download_list.json` and
  added `download_source_files/download_list_2.json` with jsdelivr URLs, confirming
  the index-based approach is already broken against upstream HEAD.
- **Verified (user, in chat):** the new TPR app reads `download_list_2.json`; older
  TPR versions still read `download_list.json` — both need updating for now.
- **Assumption:** we do not update the `resources/tpr_downloads` git submodule
  pointer as part of this thread (no git commands run except by explicit user
  request, per project rules) — this thread only changes DPD's own Python code so
  that whenever the submodule *is* later updated/pulled, our writer behaves
  correctly against either file. `download_list_2.json` won't exist locally until
  the submodule is updated; the code must not crash when it's absent.
- **Assumption:** matching by URL-suffix (`.../release_zips/dpd.zip` /
  `.../release_zips/dpd_beta.zip`) remains unique and stable — confirmed by
  grepping the current file: only these two entries' URLs end that way.
- **Confirmed (user, in chat):** if a matching entry isn't found in a given file
  (e.g. `download_list_2.json` has no beta entry) the code should warn and skip,
  not append a new entry — the user confirmed a beta entry there isn't necessary.

## Constraints
- No `sys.path` hacks; modern type hints; `pathlib.Path` (already the case in this
  file).
- Don't touch the submodule content or its `.gitmodules` entry.
- Preserve existing `pr` (printer) messaging style and existing function
  signature/behavior for callers (`main()` in the same file calls
  `copy_zip_to_tpr_downloads(g)` with no argument changes).
- Minimal change — no refactor of unrelated parts of `tpr_exporter.py`.

## How we'll know it's done
- A new unit test in `tests/exporter/tpr/test_tpr_exporter.py` exercises the
  entry-lookup + URL-rewrite logic against small fixture JSON files (not the real
  submodule), covering: found-by-suffix update, missing-file skip, entry-not-found
  skip.
- `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright` clean on both
  changed files.
- `uv run pytest tests/exporter/tpr/` and `tests/tools/` (for `paths.py` coverage
  if any) pass.

## What's not included
- Updating the `resources/tpr_downloads` submodule pointer / pulling upstream
  changes.
- The future "attach DPD as a secondary DB" install-speed change bksubhuti
  mentioned — that's a separate, not-yet-specified future thread.
- Inserting new entries into `download_list_2.json` when no matching entry exists
  yet (confirmed unnecessary for beta).
