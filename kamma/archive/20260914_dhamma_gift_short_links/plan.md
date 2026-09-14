# Plan: Dhamma.gift short links

Spec: `spec.md` in this directory.

## Baseline (recorded before any edit)
- `uv run pytest tests/` — 1858 passed, 12 deselected. No pre-existing failures.
- `just typecheck` (pyrefly) — 0 errors.
- Working tree carries unrelated changes from other sessions: `kamma/lessons.md`
  (modified) and `exporter/kindle/kindling-cli` (untracked). Not this thread's;
  never stage them.

## Phase 1 — dpd-db (webapp + GoldenDict share one property)

- [x] **1.1 Switch the link builder.** `db/models.py`, `SuttaInfo.dhamma_gift`:
  emit `https://dhamma.gift/{sc_code.lower()}`.
  → verify: `uv run pytest tests/exporter/webapp/test_dpd_headword.py` passes and
  the rendered HTML carries the new form.
  *Done. One-line change; `tbw_legacy` untouched.*

- [x] **1.2 Update the stale webapp assertion.**
  `tests/exporter/webapp/test_dpd_headword.py:172` still expected the old
  `read/?q=SN1.1` form.
  → verify: that test file passes.
  *Done.*

- [x] **1.3 Add property-level tests.** `tests/db/test_sutta_info.py` had none —
  coverage was only indirect through rendered HTML, on one already-lowercase code.
  Cover plain, range and Khuddaka shapes plus the `None` branch.
  → verify: `uv run pytest tests/db/test_sutta_info.py` — 16 passed.
  *Done.*

- [x] **1.4 Cover the GoldenDict render.** Its fixture passes `dhamma_gift=None`,
  so nothing asserts the link that export actually emits. Add a test in
  `tests/exporter/goldendict/test_dpd_headword.py` mirroring the webapp one.
  → verify: `uv run pytest tests/exporter/goldendict/test_dpd_headword.py` — 27
  passed. *Done — but note it asserts the template renders whatever the property
  hands it (the fixture supplies a stub URL); the builder itself is covered by 1.3.*

- [x] **1.5 Repo gates.** `uv run ruff check --fix`, `uv run ruff format`,
  `uv run pyright` on each touched file, then `uv run pytest tests/` and
  `just typecheck`.
  → verify: ruff clean, ruff format left all 4 files unchanged, pyright 0 errors,
  `uv run pytest tests/` 1862 passed / 12 deselected, `just typecheck` 0 errors,
  `flutter test` 388 passed in the sibling repo. *Done.*

## Phase 2 — Flutter app (sibling repo `../dpd-flutter-app`)

Separate repo, separate commit. **Needs the user's go-ahead before editing** —
it is outside this working tree.

- [x] **2.1 Switch the Dart getter.** `lib/database/sutta_info_extensions.dart:69`,
  `dhammaGift`: emit `https://dhamma.gift/${scCode!.toLowerCase()}`. Leave
  `tbwLegacy` (lines 181-182) alone.
  → verify: `flutter analyze` on the two touched files — no issues. (Repo-wide
  `flutter analyze` reports 52 pre-existing issues, none in these files.) *Done.*

- [x] **2.2 Update its test.**
  `test/database/sutta_info_extensions_test.dart:22-26` asserts the old
  `f.dhamma.gift/read/?q=SN35.28` form; it must assert `dhamma.gift/sn35.28` and
  cover the lowercasing.
  → verify: `flutter test` — 15 passed. *Done; added a range-code case too.*

- [x] **2.3 Changelog.** `assets/help/changelog.json` records the previous host
  swap; add the matching entry for this one if the repo's convention expects it.
  → verify: JSON parses; entry added to the `unreleased` section. *Done.*

## Phase 3 — Report, do not fix

- [x] **3.1 Report the three dead sutta codes** from the spec's verified facts
  (`DHP90-00` typo, the 11 bare `AN<n>` nipāta rows, `SN12.93-103`). The typo is a
  real DPD data bug that also breaks that row's SuttaCentral and Buddha's Words
  links — the user decides whether it gets its own thread.

- [x] **3.2 Docs page.** User decided (2026-09-14): the forms in the webadmin's
  email are correct and the docs are simply stale. Swapped the `read.php` reader
  link to a short-form sutta link, and the `find.dhamma.gift` host in `README.md`
  to the bare domain. `docs/newsletters.md` left alone — published history.

- [x] **3.3 Older-host leftovers.** `README.md:39` fixed under 3.2.
  `docs/newsletters.md:850` left on `find.dhamma.gift` — published newsletter
  history, not a live link DPD generates.

## Review and finalize
- [ ] Independent subagent review + CodeRabbit, in parallel.
- [ ] Fix blocking/major findings, re-verify.
- [ ] Propose commit messages (one per repo). Do not commit unasked.

## Review findings addressed (pi / deepseek-v4-pro, 2026-09-14)
- **Range-code verification was overstated** — it proved content existed, not that
  it was the *right* sutta. Re-ran with title comparison: 109 matched, 79 have no
  DPD name to compare, 0 differed, 2 were the already-named 404s. Spec corrected.
- **Row count was off by one** — 5115 rows, one with an empty `sc_code`. Corrected.
- **GoldenDict test over-claimed** — it feeds the template a stub URL and would not
  fail on a revert. Spec now says so plainly instead of implying coverage.
- **Spec contradicted the implementation** on the two doc files; the mid-thread
  scope change is now recorded in the spec, not only in this plan.
- **Changelog carried two contradictory unreleased entries** — the older one now
  names the Buddha's Words mirror, which is what it still describes.

## Deviations from the original approach
- **2026-09-14:** `dart format` on the two touched Dart files reformatted ~80
  unrelated lines (formatter version newer than the repo's style). Reverted both
  files and reapplied the edits without it; the diff is now 2 + 15 lines.
- **2026-09-14:** The first pass scoped this from a single grep hit and covered
  only surface 1, missing the GoldenDict test gap and the Flutter repo entirely.
  The archived thread `20260731_dhamma_gift_domain` names all three surfaces and
  should have been read first. Phases 1.4 and 2 exist because of that miss.
