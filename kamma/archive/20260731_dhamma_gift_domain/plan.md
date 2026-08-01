# Plan: Swap find.dhamma.gift → f.dhamma.gift

## GitHub issue
None referenced.

## Architecture Decisions
- Change the host once in the shared `db/models.py` cached properties
  (`dhamma_gift`, `tbw_legacy`) — both webapp and GoldenDict exporter render
  links from these same properties, so one edit covers two of the three places.
- Keep URL path structure byte-identical; swap only the hostname.
- Flutter app maintains its own mirror getters (`dhammaGift`, `tbwLegacy`) in
  `sutta_info_extensions.dart` — update them there; they deliberately
  reimplement the Python logic per project convention.
- No template changes needed: `dpd_headword.html` / `dpd_headword.jinja` only
  contain the display label "Dhamma.gift", not the host.

## Phase 1 — Python side (dpd-db)
- [x] Update `db/models.py` `dhamma_gift` (line ~857) and `tbw_legacy`
      (lines ~905/907) to use `f.dhamma.gift`
      → verify: `rg "find\.dhamma\.gift" db/models.py` returns no matches
- [x] Update `tests/exporter/webapp/test_dpd_headword.py` expected URL
      → verify: `uv run pytest tests/exporter/webapp/test_dpd_headword.py -q` passes
- [x] Update `tests/exporter/goldendict/test_dpd_headword.py` expected URLs (3)
      → verify: `uv run pytest tests/exporter/goldendict/test_dpd_headword.py -q` passes
- [x] Lint: ruff check/format + pyright on all 3 touched Python files
      → verify: all three tools exit clean

## Phase 2 — Flutter side (dpd-flutter-app)
- [x] Update `lib/database/sutta_info_extensions.dart` `dhammaGift` +
      `tbwLegacy` (lines ~69/181/182) to `f.dhamma.gift`
      → verify: `rg "find\.dhamma\.gift" lib/` returns no matches
- [x] Add tests to `test/database/sutta_info_extensions_test.dart` for
      `dhammaGift` and `tbwLegacy` asserting the new host
      → verify: `flutter test test/database/sutta_info_extensions_test.dart` passes
- [x] `flutter analyze` clean on the touched files
      → verify: no new analyzer issues

## Phase 3 — Full verification
- [x] Sweep both repos: `rg --hidden "find\.dhamma\.gift"` in the five scoped
      files → zero matches; remaining hits only in out-of-scope data/docs
      → verify: exit code 1 (no matches) in scoped paths
- [x] Full test suite: `uv run pytest tests/ -q` (dpd-db) + `flutter test`
      (app) → all pass

## Finalize
- [ ] Archive thread
