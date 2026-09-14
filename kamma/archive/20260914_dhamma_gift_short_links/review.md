## Thread
- **ID:** 20260914_dhamma_gift_short_links
- **Objective:** Switch DPD's generated Dhamma.gift sutta links to the site's new short path form.

## Files Changed
**dpd-db**
- `db/models.py` — `SuttaInfo.dhamma_gift` now emits `https://dhamma.gift/<sc_code lowercased>`
- `tests/db/test_sutta_info.py` — parametrized property tests: 5 code shapes, `None`, empty string
- `tests/exporter/webapp/test_dpd_headword.py` — own default-path test for the link; TBW test no longer carries it
- `tests/exporter/goldendict/test_dpd_headword.py` — link row test, fed by the real property
- `docs/integrations/dhamma_gift.md` — reader bullet off the retired `read.php`
- `README.md` — off the older `find.dhamma.gift` host
- `kamma/threads/20260914_dhamma_gift_short_links/{spec,plan}.md` — thread files

**dpd-flutter-app**
- `lib/database/sutta_info_extensions.dart` — `dhammaGift` getter, same form
- `test/database/sutta_info_extensions_test.dart` — short form, range code, empty string
- `assets/help/changelog.json` — entry added; superseded entry reworded to name the mirror

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | blocking | git index | 3 files staged, 4 test files not; no `git add` was run by this thread | A commit from that index ships the link change without its tests | Reported to user; index left untouched (shared tree) |
| 2 | major | `tests/exporter/goldendict/test_dpd_headword.py` | Test fed a literal URL, so it stayed green on a revert | The GoldenDict export was one of three named surfaces and was unguarded | Feed it the real `SuttaInfo.dhamma_gift` |
| 3 | minor | `tests/db/test_sutta_info.py`, `sutta_info_extensions_test.dart` | Only the `None` branch covered | One live row has an empty-string `sc_code` — the case that actually occurs | Added empty-string cases both sides |
| 4 | minor | `tests/exporter/webapp/test_dpd_headword.py` | Link assertion parked inside the TBW toggle test | The row is not gated on that flag; default path had no assertion | Own test at `show_tbw=False` |
| 5 | minor | `spec.md` | Exclusions had run on into the "scope added" list | Spec asserted 4 carriers were edited that were not | Moved back under exclusions |
| 6 | minor | `spec.md` | TSV exclusion misattributed and under-argued | Real reason is stronger: its URL column is never imported and the file is re-downloaded each build | Recorded the real reason |
| 7 | minor | `plan.md` | "`flutter analyze` — no issues" | Repo-wide it reports 52 pre-existing issues | Scoped the claim to the two touched files |
| 8 | nit | `tests/db/test_sutta_info.py` | 5 cases looped in one function | First failure hides the rest | Parametrized |
| 9 | nit | `tests/exporter/goldendict/test_dpd_headword.py` | Missing return annotations | Repo rule: type hints everywhere | Added |
| 10 | nit | `docs/integrations/dhamma_gift.md` | Two different suttas as "the reader" on one page | Reads as an oversight | Both now `sn2.1` |

## Fixes Applied
All of 2-10. Finding 1 is reported, not acted on — the index belongs to the user.

## Test Evidence
- **Revert test** (the one that matters): `db/models.py` temporarily reverted to the old form, then restored → **7 failed, 50 passed** across the three touched test files. Before the review fixes only 4 of 8 relevant tests guarded the change; now every surface does.
- `uv run pytest tests/` (scope: whole project, 1868 tests) → pass
- `uv run pytest` on the three touched files (scope: 57 tests) → pass
- `ruff check` + `ruff format` + `pyright` (scope: the 4 touched Python files) → clean, formatter left all unchanged
- `just typecheck` (scope: whole repo, pyrefly) → 0 errors
- `flutter test` (scope: whole Flutter repo, 389 tests) → pass
- `flutter analyze` (scope: the 2 touched Dart files) → no issues; repo-wide has 52 pre-existing
- CodeRabbit `--uncommitted` (scope: 7 dpd-db files) → 0 findings
- Live site: `/api/text/<id>` — 70 codes across all 14 books (64 title matches, 4 no DPD name, 2 dead) and all 190 range codes (109 matches, 79 no DPD name, 0 wrong sutta, 2 dead)

## Not Verified
- The Flutter repo got no CodeRabbit pass — only the independent agent review.
- The site verification used its JSON endpoint, not a rendered browser page; the reader UI itself was eyeballed once for one sutta, not per code.
- 3 `sc_code` shapes (13 rows) have no text on the site — pre-existing DPD data, unrelated to this change, reported to the user and not fixed here.
- No end-to-end export was built; template-level rendering is as far as the tests go.

## Verdict
PASSED
- Review date: 2026-09-14
- Reviewer: independent subagent (zero-context) + CodeRabbit + pi/deepseek-v4-pro plan review; fixes by the implementing session
