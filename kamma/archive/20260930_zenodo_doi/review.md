## Thread
- **ID:** 20260930_zenodo_doi
- **Objective:** Put the Zenodo concept DOI into every citation surface on every build,
  local and CI, with no monthly action; make the Zenodo record carry the right metadata.

## Files Changed
- `tools/version.py` — `DOI` constant; Zenodo lookup (`get_doi`, `ensure_doi`,
  `fetch_zenodo_doi`, `_hit_is_dpd`, `ZENODO_*`, `DOI_PATTERN`) and its imports deleted
- `tools/docs_update_how_to_cite.py`, `exporter/goldendict/export_help.py`,
  `exporter/pdf/pdf_exporter.py` — `get_doi()` → `DOI`
- `.zenodo.json` — new, static; creator "Bodhirasa Bhikkhu", type dataset, no version
- `tests/tools/test_version.py` — lookup tests removed; DOI, `main()` and `.zenodo.json`
  drift tests added
- `tests/tools/test_docs_update_how_to_cite.py` — asserts the DOI on the generated page
- `tests/exporter/goldendict/test_export_help.py` — `cite` entry DOI test (review fix)
- `tests/exporter/pdf/test_pdf_exporter.py` — new; PDF citation DOI test (review fix)
- `kamma/tech.md` — citation bullet rewritten

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `tools/version.py:190`, `export_help.py:336`, `pdf_exporter.py:93` | Only the docs-page call site had a test that failed if `DOI` were dropped | `version.main()` → `db_info.citation` feeds the app and every CI export, unguarded | Added `main()`, `add_citation` and `GlobalVars` tests; each revert-checked |
| 2 | minor | `.zenodo.json` | No `version`; relies on Zenodo taking it from the tag | Unverifiable before a release | Deferred to the October check already in the spec, with a fallback |
| 3 | minor | `.zenodo.json` | Creator name has no "Family, Given" comma | Stored whole as one name; correct for a monastic name | None |
| 4 | nit | `tools/docs_update_how_to_cite.py:14` | `DOI` import out of order | Consistency | Reordered |

## Fixes Applied
- Finding 1: three behaviour tests added. Replacing `DOI` with `None` at each call site made
  its test fail (1 failed each); restored, all pass.
- Finding 4: import reordered.

## Test Evidence
- `uv run pytest tests/` (scope: whole project) → 1914 passed, 12 deselected
  (baseline 1916 − 7 deleted lookup tests + 5 new)
- `just typecheck` (scope: repo-wide pyrefly) → 0 errors, matching baseline
- `uv run pyright` + `ruff check` + `ruff format` (scope: all 8 touched `.py` files) → clean
- Revert checks (scope: docs page, `version.main()`, GoldenDict `cite`, PDF citation,
  `.zenodo.json` keyword drift) → each failed when broken, passed when restored
- CodeRabbit `review --agent --uncommitted --include-untracked` (scope: all changed and
  new files) → 0 findings
- Independent subagent review (fresh context) → findings above; `rg --hidden` sweep found
  no stale `get_doi`/`ensure_doi`/`[version] doi` references outside the thread files;
  confirmed `draft_release.yml:72` runs `tools/version.py` before the exports

## Not Verified
- How Zenodo reads `.zenodo.json` (version from tag, type Dataset, creator name) — only
  visible on the October record.
- A real uposatha build writing the DOI into `CITATION.cff`, `docs/how_to_cite.md` and
  `dpd.db`; covered by the `main()` and docs-page tests, not by a live run.
- NOTICED — NOT TOUCHING: `exporter/pdf/templates` trigger a jinja
  `DeprecationWarning: invalid escape sequence '\*'` when loaded; pre-existing.

## Verdict
PASSED
- Review date: 2026-09-30
- Reviewer: independent subagent (fresh context) + CodeRabbit CLI; fixes by the
  implementing agent, re-verified above.
