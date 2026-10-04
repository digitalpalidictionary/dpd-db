# Handoff: Wikipedia Buddhist Encyclopedia (other-dictionaries)

Rewritten 2026-10-04 (session 3). Supersedes the session-2 handoff, whose
"dead ends" and "viable paths" sections are resolved — see plan.md 2.1–2.5.

## Status

Phase 2 build DONE and machine-verified; waiting on the user's GoldenDict
check of 10 random entries (plan.md 2.5), then `/kamma:3-review`.

- Builds: `resources/other-dictionaries/build/goldendict/wikipedia.zip` and
  `build/mdict/wikipedia.zip`, ~58 MB each, 23,837 entries, 64,153 synonyms.
- Scope: Category:Buddhism walked to depth 5 (user decision; full tree drifts
  off topic). 23,840 articles listed, 23,836 fetched.
- Route: list + redirects from the 20261001 SQL dumps, text from the action
  API (user decision; 25 GB pages-articles dump abandoned at 6.4 GB, kept).

## What session 3 found (all verified, details in plan.md)

- `categorylinks.cl_target_id` → `linktarget.lt_id` (MediaWiki 1.45), not a
  page id. That was the whole 0-result walk.
- `fetch_from_dump.py` would have matched 0 titles (`"}title"` is not valid
  ElementTree syntax) and collected no redirects. Fixed + tested; now unused.
- Link resolution missed lowercase/underscore targets; unpiped labels showed
  the redirect target instead of the written text. Fixed + tested.
- Whole-build scan: parser functions, `<references/>`, `<imagemap>` and the
  About entry's raw `'''` leaked. Fixed + tested. ~1% residue left (plan 2.5).

## Re-running

`./dictionaries/wikipedia/run_overnight.sh` from `resources/other-dictionaries`
(dumps pinned to 20261001; resumable). Keep the sum of concurrent downloads
≤ 400 KB/s — the user's line is shared. Never delete files in `source/dumps/`.

## Not committed

Nothing in the submodule is committed (Phase 1 or 2). The user commits.
