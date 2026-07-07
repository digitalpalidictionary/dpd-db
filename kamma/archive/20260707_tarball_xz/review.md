# Review: Release db artifact bz2 → xz

**Verdict: PASSED** (2026-07-07)

Independent zero-context reviewer (Sonnet subagent) + main-thread verification.

## Files changed

- `scripts/build/tarball_db.py` — rewritten: `tar -I 'xz -9e -T0'` subprocess, writes `dpd.db.tar.xz` directly to share_dir
- `scripts/onboarding/contributor_setup.py` — new `extract_database()` (tarfile `r:xz`, `filter="data"`, archive always unlinked); setup downloads archive then extracts
- `scripts/onboarding/contributor_update.py` — same download-then-extract flow
- `tests/scripts/onboarding/test_contributor_setup.py` — fixtures → tar.xz, new `TestExtractDatabase` (3 real-tarfile tests), 4 full-flow tests patched for the new step
- `tests/scripts/onboarding/test_contributor_update.py` — fixtures + extract mock
- Mechanical: `draft_release.yml` (2), `mobile_release.yml` (3), `justfile`, `update-dpd.sh`, `CONTRIBUTING.md` (2), `docs/technical/{use_db,quick_start,local_server_setup}.md`, `.gitignore`

## Findings

None blocking/major. Reviewer verified empirically:
- `tar -cf <path> -C <dir>` argument resolution and bare `dpd.db` member name (matches `extract_database` expectation)
- `filter="data"` valid on Python 3.12/3.13 (read stdlib source)
- `KeyError` on missing member caught; archive unlinked in `finally` on all paths
- `tools/tarballer.py` NOT dead code (still used by audio + deconstructor tarballs)
- Consumer sweep zero hits for `dpd.db.tar.bz2` / `tar -xj` outside historical paths
- `docs/newsletters.md` old links will 404 after next release — spec-accepted (historical record)

Also fixed in passing (in spec scope): pre-existing onboarding bug where the
downloaded tarball bytes were written directly to `dpd.db` with no extraction.

## Test evidence

- Production command on live 2.2GB db: **184 MB in 230s** (vs 208 MB / 357s bz2); extraction byte-identical
- xz memory limiter auto-reduced threads 22 → 6 — graceful on small CI runners
- `pytest tests/scripts/onboarding/`: 86 passed; full suite: **1232 passed**
- ruff check / format / pyright clean on all touched .py files
