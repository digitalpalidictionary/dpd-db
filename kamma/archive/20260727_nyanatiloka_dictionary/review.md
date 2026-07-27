## Thread
- **ID:** 20260727_nyanatiloka_dictionary
- **Objective:** Add Nyanatiloka Mahathera's *Buddhist Dictionary* (1,406 entries, scraped from dhammatalks.net) as a standalone `dict_id = "nyanatiloka"` dictionary to `resources/other-dictionaries` (GoldenDict/MDict) and the DPD mobile SQLite export.

## Files Changed
- `dpd-db/exporter/mobile/mobile_exporter.py` — new Nyanatiloka block in `export_other_dictionaries`, inserted after the (sibling-thread) Apte block
- `dpd-db/tools/paths.py` — `nyanatiloka_source_path` / `nyanatiloka_css_path`
- `dpd-db/docs/other_dicts.md`, `dpd-db/docs/index.md` — dictionary tables + description section
- `other-dictionaries/dictionaries/nyanatiloka/{nyanatiloka.py,nyanatiloka.css,README.md,__init__.py,nyanatiloka.tar.zst}` — new dictionary package (source/ gitignored, tar.zst tracked)
- `other-dictionaries/vendor/dpd_tools/paths.py` — `_setup_nyanatiloka_paths`
- `other-dictionaries/scripts/prepare_sources.py`, `scripts/export_all.py` — registered as mobile-critical + build-all
- `other-dictionaries/.github/workflows/build-and-release.yml`, `README.md` — release notes table + dict table row
- `dpd-flutter-app/assets/help/bibliography.tsv` — bibliography row
- `dpd-flutter-app/justfile` — `build-db` recipe flags corrected to match `dpd-db`'s own `export-mobile` recipe (both now `--cone` only; `--peu`/`--wordnet` no longer exist as CLI flags in `mobile_exporter.py`, confirmed by reading its argparse — the memory note describing `--cone --peu --wordnet` as the required set predates that removal, not a conflict with this thread's fix)

## Findings

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `exporter/mobile/mobile_exporter.py` (Nyanatiloka block, `nyanatiloka_css.read_text(...)`) | Unlike the DPPN/Apte/CPD/MW blocks in the same file, which all guard the CSS read with `if g.pth.X_css_path.exists(): ...` (defaulting to `""` otherwise), the Nyanatiloka block reads `nyanatiloka_css_path.read_text()` unconditionally | Harmless today since `nyanatiloka.css` is committed and always present, but it's the one block in this function that would raise `FileNotFoundError` instead of degrading gracefully if the file were ever missing/renamed — inconsistent with every sibling block's defensive pattern | Wrap in the same `if path.exists(): css = _sanitize_css(...)` pattern used by DPPN/Apte, or leave as-is and note the asymmetry is accepted (spec's code snippet already shows it unconditional, so this may be an intentional simplification — flagging for awareness, not requiring a change) |

No other findings. Spec and plan are internally consistent, and both self-corrected mistakes recorded in `plan.md` (single-HTML-shape assumption; unscoped `compress_sources.py` run) show clean, verifiable resolution in the current working tree (no spurious `.tar.zst` diffs on `cpd`/`peu`/`wordnet`, no stray `apte.tar.zst`/`mw.tar.zst`).

## Fixes Applied
- Finding #1 (CSS read not guarded with `.exists()`): fixed after all — wrapped in the same `if path.exists(): css = _sanitize_css(...)` pattern used by DPPN/Apte/CPD/MW. Re-ran ruff/pyright on `exporter/mobile/mobile_exporter.py` afterward, both clean.
- CodeRabbit (run separately after this review, via isolated `git worktree` per repo to scope out concurrent-thread noise — see below) found 2 minor issues in `other-dictionaries/dictionaries/nyanatiloka/README.md`: it asserted as fact that the source page "has not changed since 2005" and carries "no reuse restriction," when the actual evidence only supports "saved 2005 per the site's own footer" and "no restriction text was found on the page." Both reworded to match what was actually verified.

## Test Evidence
- `uv run ruff check` + `uv run ruff format --check` on `exporter/mobile/mobile_exporter.py`, `tools/paths.py` → pass, no reformatting needed
- `uv run pyright exporter/mobile/mobile_exporter.py tools/paths.py` → 0 errors, 0 warnings
- `uv run ruff check` + `uv run pyright` on `other-dictionaries/dictionaries/nyanatiloka/`, `vendor/dpd_tools/paths.py`, `scripts/prepare_sources.py`, `scripts/export_all.py` → ruff pass; pyright not installed in submodule's env (no `.pre-commit-config.yaml` there either — separate repo, own tooling, not part of dpd-db's gate)
- `uv run pytest tests/ -k "mobile or paths"` → 15 passed
- `uv run python -m dictionaries.nyanatiloka.nyanatiloka` (fresh run in submodule) → clean, produces `build/goldendict/nyanatiloka.zip` and `build/mdict/nyanatiloka.zip`, gitignored `build/` confirmed clean afterward
- Independent data audit of `dictionaries/nyanatiloka/source/nyanatiloka.json` (1,406 entries): 0 leftover `<a>`/`<font>` tags, 0 unresolved `&#…;` entities, 0 near-empty bodies, exactly one duplicate headword (`conception` ×2, as claimed), no stray `-A-`-style divider or "BUDDHIST DICTIONARY" pseudo-entries — all claims in spec.md/plan.md independently reproduced, not just trusted
- Confirmed `nyanatiloka` block in `mobile_exporter.py` is unconditional (only `include_cone` is flag-gated) — matches the spec's "ships enabled by default" constraint
- Confirmed no `DB_SCHEMA_VERSION` bump
- Confirmed `source/` is gitignored and `.tar.zst` is tracked via the submodule's existing glob-negation `.gitignore` rules — no new registration needed, as claimed
- `coderabbit review --agent` — rate-limited during this review (free CLI allowance exhausted); manual review above was correspondingly more thorough to compensate. Run afterward, separately, scoped per-repo via isolated `git worktree` copies (only this thread's files, to exclude other concurrent threads' uncommitted changes in the same working tree): `dpd-db` 0 findings, `other-dictionaries` 2 minor findings (fixed, see above), `dpd-flutter-app` 0 findings.

## Verdict
PASSED
- Review date: 2026-07-27
- Reviewer: Claude (fresh session, kamma:3-review)
