# Review: Add s.4nt.org to sutta links

## Round 2 correction (sutta-level precision)
The round-1 design (this file's original content below) verified page-level
paths only and shipped in commit 9ab17694. The user tested it live on
SN12.5 and rejected it: it landed on the 300-entry SN12 container page with
no way to jump to the individual sutta, defeating the entire point of a
"one code takes you to that sutta" link.

Root cause: the site's own embedded JS (`jumpToRef`/`jumpToHash` in a
container page's `<script>`) was never read. It defines a real, supported
`#<id>` deep-link scheme (confirmed by the source comment `an3.65) → a
sutta group header`) that round 1 never looked for.

### Verification (this round)
- Extracted every real TOC anchor `id` from every SN/AN/KN container page
  in the cloned repo (`~/MyFiles/2_Resources/Code/s.4nt/`).
- Cross-checked against all 4,678 real `sc_code` rows in `dpd.db` that
  produce a fragmented link, via the actual `s_4nt_link` property (not a
  throwaway script) - **0 mismatches**.
- 45 exceptions (19 SN/AN peyyala-range, 26 DHP vagga-range) pinned in
  `_S4NT_ANCHOR_OVERRIDES`, each verified against the real page content.
- 4 live HTTP spot-checks (including a peyyala-range case and a DHP
  vagga-range case) - all 200 OK.
- ruff check + ruff format + pyright: clean on `db/models.py` and
  `tests/db/test_sutta_info.py`.
- `tests/db/test_sutta_info.py` (14 cases, 5 new for the override/precision
  branches) + `tests/exporter/{goldendict,webapp}/test_dpd_headword.py`:
  34 passed.

## Outcome: PASS

---

## Round 1 (superseded - kept for history)

## Verification (in lieu of a completed CodeRabbit pass)
CodeRabbit review was started via subagent but stopped by the user before
completing. In its place, the design was verified against ground truth:

- Site's actual source repo (github.com/frankksutta/s.4nt, a static GitHub
  Pages export - the committed file tree IS the complete list of valid
  URLs) cloned to `~/MyFiles/2_Resources/Code/s.4nt/`.
- Every one of the 5,114 real `sc_code` rows in `dpd.db` cross-checked
  against that file tree via the actual `s_4nt_link` property - 0
  mismatches.
- 15+ live HTTP spot-checks, all 200 OK.
- CodeRabbit's one earlier valid finding (missing `tha-ap`/`thi-ap` KN book
  codes) was incorporated after being initially wrongly dismissed as a
  hallucination.

## Verification (standard gates)
- ruff check + ruff format + pyright: clean on all touched files.
- `tests/db/test_sutta_info.py` (10 new/updated cases) +
  `tests/exporter/{goldendict,webapp}/test_dpd_headword.py`: 31 passed.

## Outcome: PASS
