# Review: 20260731_dhamma_gift_domain

## Thread
- **ID:** 20260731_dhamma_gift_domain
- **Objective:** Swap `find.dhamma.gift` → `f.dhamma.gift` in all three DPD link generators (webapp, GoldenDict exporter, Flutter app) per webadmin request — avoids Cloudflare captcha, faster, works without VPN.

## Files Changed
- `db/models.py` — `dhamma_gift` + `tbw_legacy` cached properties now emit `f.dhamma.gift` (feeds both webapp and GoldenDict templates)
- `tests/exporter/webapp/test_dpd_headword.py` — updated expected URL; added assertion covering the `dhamma_gift` read link
- `tests/exporter/goldendict/test_dpd_headword.py` — updated 3 expected URLs (hidden/show/legacy toggle tests)
- `../dpd-flutter-app/lib/database/sutta_info_extensions.dart` — mirrored `dhammaGift` + `tbwLegacy` getters now emit `f.dhamma.gift`
- `../dpd-flutter-app/test/database/sutta_info_extensions_test.dart` — 6 new tests (host, iti special case, null scCode, unsupported book code)

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `tests/exporter/webapp/test_dpd_headword.py` | `dhamma_gift` host change not asserted on real model | The webapp test only checked `tbw_legacy`; goldendict test stubs `dhamma_gift=None` | Added `assert "https://f.dhamma.gift/read/?q=SN1.1" in html` |
| 2 | nit | flutter `sutta_info_extensions_test.dart` | `tbwLegacy` no-scCode null branch untested | Only unsupported-book-code null case existed; scCode short-circuit distinct | Added `no scCode -> null` test mirroring `dhammaGift` |
| 3 | nit | `plan.md` Finalize | Archive checkbox unchecked | Expected — finalize runs after review | Done in 5.2 |

## Fixes Applied
- Added Python-side assertion for the swapped `dhamma_gift` host on the real `SuttaInfo` model.
- Added flutter `tbwLegacy` null-scCode test.
- Re-ran lint + tests after each fix (ruff/pyright clean; both suites green).

## Test Evidence
- `uv run pytest tests/ -q` → 1752 passed, 12 deselected
- `flutter test` (dpd-flutter-app) → all passed
- `uv run ruff check/format` + `uv run pyright` on touched Python files → clean
- `flutter analyze` on touched Dart files → no issues
- Live check: `f.dhamma.gift/read/?q=sn1.1` and `f.dhamma.gift/bw/sn/sn1.1.html` both return 200
- Sweep: zero `find.dhamma.gift` matches in all scoped files (exit 1)

## Verdict
PASSED
- Review date: 2026-07-31
- Reviewer: independent subagent (via subagent tool), fixes applied inline
