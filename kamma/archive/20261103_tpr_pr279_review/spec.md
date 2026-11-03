# Spec — PR #279 review and TPR handover

PR: https://github.com/digitalpalidictionary/dpd-db/pull/279 (bksubhuti, "TPR: all-in-one DPD package, and both TPR zips served from a release").

## Overview

PR #279 moves the TPR zips to a GitHub release (jsDelivr refuses `dpd.zip` at 23.5 MB) and adds `exporter/tpr/tpr_package.py`, an all-in-one SQLite package for TPR build 129+. The review (`review.md`, `egm/gate1.md`) found that nearly all of its risk sits in DPD's release workflow uploading into `bksubhuti/tpr_downloads`, and that the package needs only `dpd.db`, which every DPD release ships as `dpd.db.tar.xz`.

The owner decided (2026-11-03) not to merge it, and to hand the whole TPR build to the author.

## What it should do

1. Post the agreed reply on PR #279 in the owner's name, with no signature. Keep the PR open. The posted comment is the record: https://github.com/digitalpalidictionary/dpd-db/pull/279#issuecomment-6601345237
2. Leave DPD's TPR export running unchanged until the author says his own build works.
3. Then, in a separate thread, take TPR out of DPD completely.

## Decisions (owner)

- The TPR build lives with the author. He builds from the latest DPD release whenever he ships a TPR version, plus an optional uposatha-day workflow for the download list.
- DPD switches its TPR export off only once the author's build is up and working. There is no fixed date.
- The reply includes a details section for building it with Claude Code.

## Facts verified

See `egm/brief.md` and `egm/gate1.md`. Also:
- Release tags look like `v0.4.20261026`, and `dpd.db.tar.xz` holds `dpd.db` at the top level (`scripts/build/tarball_db.py`).
- `exporter/tpr/templates/tpr_headword.jinja` reads `i.variant`; the `variant` column is empty in all 89,774 rows (moved to `var_text`).
- Not every DPD release falls on an uposatha day (12 June 2026). The reply points to the uposatha calendar.
- The current exporter's list updates match on `release_zips/dpd.zip`, which no longer matches the hand-edited upstream URLs, so they skip silently.

## Removal scope for the later thread (from a sweep on 2026-11-03)

`.github/workflows/draft_release.yml` (TPR step and the tpr_downloads sync, collect and push legs), `.gitmodules` + `resources/tpr_downloads`, `exporter/tpr/`, `tests/exporter/tpr/`, `tools/paths.py` (tpr paths), `tools/configger.py` (`make_tpr`, `[tpr]`), `tests/tools/test_configger_fixtures.json`, `justfile` (`export-tpr`), `scripts/bash/makedict.py`, `scripts/onboarding/contributor_setup.py`, `scripts/build/config_quick_profile.py`, `scripts/server_contrib/config_server.template`, `scripts/server_contrib/maintenance_window.py` (mentions `i2h.tsv`), `db/families/family_root.py` and `family_compound.py` (`make_tpr` gate), `db/inflections/inflections_to_headwords.py` (`save_i2h_for_tpr`), `AGENTS.md`, `.gitignore`, `.graphifyignore`. Open question for that thread: the owner's local TPR db copy (`[tpr] db_path`) goes with the exporter. Ask before removing it.

## How we'll know it's done

- The reply is on PR #279 from `bdhrs`, and the PR is still open.
- This thread is finalized. The removal thread is opened only after the author confirms his build works.

## What's not included

- Any code change in DPD now.
- Building or testing the author's workflow.

## Review record

Gate 1: 6 Goldfish on pi / azure `deepseek-v4.1-flash` (one retry after 429s), 30 findings: 19 accepted, 4 escalated, 7 rejected (`egm/gate1.md`). Gates 2 and 3 were not run: the owner turned the thread from "fix the PR" into "hand over and reply", which leaves no code spec to attack.
