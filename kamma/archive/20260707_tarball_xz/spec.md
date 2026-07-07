# Spec: Release db artifact bz2 → xz (dpd.db.tar.xz)

**GitHub issue:** #157 (refactoring/optimization umbrella)

## Overview

Replace the `dpd.db.tar.bz2` release artifact with `dpd.db.tar.xz` compressed via
`xz -9e -T0`. The user's criterion, settled after testing: **smallest file within
the current build-time budget (≤357s)**.

Measured on the real 2.2GB db (2026-07-07):

| method | size | time | notes |
|---|---|---|---|
| zstd -22 --long=31 | 179MB | 429s | DQ: over time budget + needs `--long` flag to decompress |
| **xz -9e -T0** | **184MB** | **269s** | winner |
| xz -9 -T0 | 190MB | 209s | fallback if CI time is a problem |
| bzip2 -9 (current) | 208MB | 357s | baseline |
| zip -6 | 313MB | 35s | rejected: +50% download size |

Adoption verified: Windows 11 (23H2+) extracts `.tar.xz` natively in File Explorer;
Windows 10 via 7-Zip (xz supported for ~15 years); macOS Finder opens `.tar.xz`
(CLI `tar -xf` always); xz-utils is effectively mandatory on all Linux distros.
Every in-repo `| tar -xj` pipe becomes `| tar -xJ` — xz streams fine from stdin.

## What it should do

### 1. Producer: `scripts/build/tarball_db.py`

Replace `create_tarball(..., compression="bz2")` with a subprocess call:
`tar -I 'xz -9e -T0' -cf dpd.db.tar.xz -C <root> dpd.db`, output moved to
`pth.share_dir` as today. Keep the script name, the `[exporter] tarball_db`
config gate, and the printer output shape. **Python's stdlib `tarfile w:xz`
cannot be used** — its `lzma` is single-threaded (~25 min).
`tools/tarballer.py` stays untouched (still used by the deconstructor tarball).

### 2. Onboarding scripts: fix latent no-extraction bug

`scripts/onboarding/contributor_setup.py` and `contributor_update.py` currently
download the matched release asset (the *tarball*) **directly to `dpd.db` with no
extraction** — writing archive bytes as the sqlite file. Pre-existing bug, must be
fixed as part of this change: download to `dpd.db.tar.xz` in the project root,
extract `dpd.db` with stdlib `tarfile` (`r:xz`, `filter="data"`), delete the archive.
The asset matcher (`"dpd.db" in asset["name"]`) still matches the new name.

### 3. Consumers: name + flag updates (complete carrier list from swept repo)

- `.github/workflows/draft_release.yml` — asset path in upload list and release files (2 refs)
- `.github/workflows/mobile_release.yml` — comment (line 9), `gh release download --pattern` + `tar -xjf` block (lines 91–93)
- `justfile` (line 278, update recipe) — `tar -xj` → `tar -xJ`, name
- `scripts/server/update-dpd.sh` (line 23) — same
- `CONTRIBUTING.md` (lines 179, 183) — same
- `docs/technical/use_db.md` (line 12), `quick_start.md` (line 14), `local_server_setup.md` (line 40)
- `.gitignore` (line 52) — `dpd.db.tar.bz2` → `dpd.db.tar.xz`
- `tests/scripts/onboarding/test_contributor_setup.py`, `test_contributor_update.py` — update for the new download+extract flow

NOT changed: `docs/newsletters.md` + `scripts/build/newsletter_processed.json`
(historical record), `conductor/tracks/**` (archived planning docs),
`archive/**`, `tools/tarballer.py`, `[exporter] tarball_db` config key
(a .tar.xz is still a tarball; renaming ripples through configger PROFILES,
fixtures, and users' config.ini for zero benefit), `scripts/build/README.md`
mention of "tarballing" (still accurate).

## Assumptions & uncertainties

- `xz` CLI is present locally (verified, 5.4.5) and on ubuntu-latest runners (standard).
- **CI time uncertainty:** 269s was measured on 22 cores; the GitHub runner has 4.
  `xz -9e` may exceed the runner's current bz2 time. Accepted by user; fallback is
  `xz -9 -T0` (one-character change). First release build will tell.
- External consumers' scripts fetching `releases/latest/download/dpd.db.tar.bz2`
  break once at the next release. Accepted — old releases keep the old asset.
- Stdlib `tarfile r:xz` decompression (onboarding) is single-threaded but fast
  enough (~30–60s) for a one-time setup step.

## Constraints

- Must work in local makedict AND GitHub Actions (Python 3.12, ubuntu runners).
- No new Python dependencies; extraction uses stdlib `tarfile`.
- All touched files pass ruff check, ruff format, pyright; full pytest suite green.

## How we'll know it's done

1. `tar -I 'xz -9e -T0'` roundtrip on the real db: extracts byte-identical, size ≈184MB, time ≤357s.
2. Onboarding download+extract flow covered by updated tests (mocked download, real tarfile extraction of a small fixture).
3. `rg --hidden "dpd\.db\.tar\.bz2|tar -xj"` over the repo (excluding historical/archive paths) returns nothing.
4. Full test suite passes.

## What's not included

- Renaming the config key or script (`tarball_db` stays).
- The audio db tarball (`dpd_audio_*.tar.gz`) and deconstructor output tarball — different artifacts.
- Shipping both formats for a transition period (user accepted the one-time break).
