# Plan: Release db artifact bz2 → xz

**Spec:** ./spec.md · **Issue:** #157

## Architecture Decisions

- **`xz -9e -T0` via `tar -I`** — one subprocess, no shell pipe, no stdlib tarfile
  (Python lzma is single-threaded, ~25 min). Fallback documented: `xz -9 -T0`.
- **Keep `tarball_db.py` name and `[exporter] tarball_db` config key** — a .tar.xz
  is still a tarball; renaming ripples through configger PROFILES, test fixtures,
  and existing users' config.ini for zero benefit.
- **`tools/tarballer.py` untouched** — still used by deconstructor output tarball.
- **Onboarding extraction via stdlib `tarfile` (`r:xz`, `filter="data"`)** — new
  `extract_database()` in contributor_setup.py, reused by contributor_update.py
  (which already imports `download_database` from setup).
- **Historical docs (newsletters, conductor tracks, archive/) stay bz2** — they
  record the past.

## Phase 1 — Producer

- [x] `scripts/build/tarball_db.py`: replace `create_tarball(...)` with
  `subprocess.run(["tar", "-I", "xz -9e -T0", "-cf", <share_dir>/dpd.db.tar.xz, "-C", <root>, "dpd.db"], check=True)`;
  keep config gate and printer lines (tarball name in title becomes dpd.db.tar.xz; print size in MB after)
  → verify: run the tar command manually against the live db into scratchpad;
    extract and `cmp` byte-identical; size ≈184MB; time ≤357s

## Phase 2 — Onboarding fix (pre-existing bug + new format)

- [x] `scripts/onboarding/contributor_setup.py`: add `extract_database(archive_path, project_root) -> bool`
  (tarfile `r:xz`, `filter="data"`, extracts `dpd.db`, unlinks archive); setup flow
  downloads to `project_root / "dpd.db.tar.xz"` then extracts
  → verify: unit test with a small real .tar.xz fixture built in tmp_path
- [x] `scripts/onboarding/contributor_update.py`: same flow via the imported helpers
  → verify: unit test same pattern
- [x] Update `tests/scripts/onboarding/test_contributor_setup.py` and
  `test_contributor_update.py`: fixture asset names → dpd.db.tar.xz, add
  extraction tests (real tarfile on tiny fixture, no mocks for the extract step)
  → verify: `uv run pytest tests/scripts/onboarding/ -q` all pass

## Phase 3 — Consumers (mechanical)

- [x] `.github/workflows/draft_release.yml`: 2 × `dpd.db.tar.bz2` → `dpd.db.tar.xz`
- [x] `.github/workflows/mobile_release.yml`: comment + download pattern + `tar -xjf` → `tar -xJf` + rm line
- [x] `justfile` update recipe: name + `tar -xj` → `tar -xJ`
- [x] `scripts/server/update-dpd.sh`: same
- [x] `CONTRIBUTING.md`: name (2 places) + `tar -xj` → `tar -xJ`
- [x] `docs/technical/use_db.md`, `quick_start.md`, `local_server_setup.md`: names + flags
- [x] `.gitignore`: `dpd.db.tar.bz2` → `dpd.db.tar.xz`
  → verify: `rg --hidden "dpd\.db\.tar\.bz2|tar -xj\b" -g '!docs/newsletters.md' -g '!scripts/build/newsletter_processed.json' -g '!conductor/**' -g '!archive/**' -g '!kamma/**' -g '!logs/**' -g '!.git/**'` returns nothing

## Phase 4 — Verification

- [x] ruff check + ruff format + pyright on every touched .py file — zero errors
- [x] `uv run pytest tests/` full suite green — 1232 passed (3 new extraction tests)
- [x] Roundtrip proof recorded (size, time, byte-identity)

## Results (2026-07-07)

- Production command on live 2.2GB db: **184 MB in 230s** (vs 208 MB / 357s bz2)
- Extraction byte-identical (`cmp`); stdlib `tarfile r:xz` reads the archive
  (proves the onboarding extract path)
- xz auto-reduced threads 22 → 6 under its memory limiter — degrades gracefully
  on the 4-core CI runner instead of failing
- Carrier sweep (`rg --hidden`) clean: zero `dpd.db.tar.bz2` / `tar -xj` refs
  outside historical paths
