# Spec — stop the monthly TPR export

Follows PR #279 (closed 2026-11-03, see `kamma/archive/20261103_tpr_pr279_review/`). Agreed there: no more monthly DPD updates for Tipitaka Pali Reader (TPR). TPR gets DPD only when its author ships a new TPR app version, built from the `dpd.db.tar.xz` of the latest DPD release.

## Overview

Today the TPR export runs automatically in two places:
- **CI** (`.github/workflows/draft_release.yml`, with `push_submodules` on uposatha days): it syncs the `resources/tpr_downloads` submodule, runs `exporter/tpr/tpr_exporter.py`, packs the submodule's changes and pushes them to `bksubhuti/tpr_downloads` `master`.
- **Locally** (`scripts/bash/makedict.py`): it runs the exporter on every build. On an uposatha day (or with `[tpr] make_beta = yes`) the exporter writes the local TPR app database (`[tpr] db_path`, set on the owner's machine), the SQL, and the zip and download lists inside the local submodule.

The goal: nothing runs the TPR export automatically any more. The code stays until the end of 2026 (promised on PR #279), then a separate thread removes it.

## What it should do

1. `draft_release.yml`: remove the "Run TPR Exporter" step; remove `resources/tpr_downloads` from the sync loop, the collect loop (and its `OUT_TPR` env) and the push loop; drop `tpr_downloads` from the `push_submodules` input description. The Dhamma Gift (`fdg_dpd`, `bw2`) and SuttaCentral (`sc-data`) legs stay as they are.
2. `scripts/bash/makedict.py`: remove `exporter/tpr/tpr_exporter.py` from `COMMANDS`.
3. Config profiles stay as they are (`make_tpr = yes`). The exporter quits unless `make_tpr = yes`, so switching the profiles off would break the manual run the owner chose to keep, and nothing calls the exporter automatically any more. (Changed during review: the first version set them to `"no"`.)
4. `tests/tools/test_configger_fixtures.json`: unrelated pre-existing fix, `make_mobile` → `"yes"` in `uposatha_reset`, to match commit 7a0d638b (2026-11-01), which changed the profile but not the fixture.
5. `docs/integrations/tpr.md` (public page): replace the "Get The Latest Version of DPD" steps (download DPD from TPR's Extensions) and the "DPD Beta Version" section with one short section: DPD updates come with each new TPR release.
6. `kamma/tech.md`: replace the TPR note (line about the jsDelivr migration) with the current state.

## Decisions (owner, 2026-11-03)

- Keep the `export-tpr` recipe in the `justfile` until the year-end removal.
- Keep the `resources/tpr_downloads` submodule until the year-end removal. CI still clones it (recursive checkout), but nothing syncs, writes or pushes it.
- A hand run of the exporter (`just export-tpr`) behaves exactly as today, including the writes to the local TPR db. Only automatic runs stop.
- Reminder for the year-end removal: the owner adds a calendar event by hand (the Google Calendar connector failed to authenticate).
- This replaces the earlier condition in `kamma/archive/20261103_tpr_pr279_review/` ("switch off only after the author's build works"). The author then said on PR #279 that he will not do monthly updates; the owner chose no monthly updates. Record: https://github.com/digitalpalidictionary/dpd-db/pull/279#issuecomment-6602325351

## Facts verified

- A sweep with `rg --hidden` for `tpr_downloads|make_tpr|make_beta|tpr_exporter|exporter/tpr|tpr_* paths|[tpr]|save_i2h_for_tpr|export-tpr|i2h.tsv` (excluding archives, `resources/`, `graphify-out/`) found the places above, plus the ones left for year end (below).
- `.github/workflows/mobile_release.yml` does not run the TPR export.
- The owner's `config.ini` has `make_tpr = yes` and a non-empty `[tpr] db_path` (checked by count, values not printed). `config.ini` is not edited by agents.
- `tests/tools/test_configger.py` compares each profile with `test_configger_fixtures.json`, so the fixture must change with the profiles.
- `AGENTS.md`'s rule about checking an upstream's default branch uses `tpr_downloads` as its example. It stays true, so it is left alone.

## Left for the year-end removal

`exporter/tpr/` and `tests/exporter/tpr/`, the `export-tpr` just recipe, the `resources/tpr_downloads` submodule (`.gitmodules`), `tools/paths.py` TPR paths, `[tpr]` and `make_tpr` defaults in `tools/configger.py`, the `make_tpr` conditions in `db/families/family_{root,word,compound,idiom,set}.py`, `save_i2h_for_tpr` in `db/inflections/inflections_to_headwords.py` (and its test), `scripts/onboarding/contributor_setup.py` and its test, `scripts/server_contrib/config_server.template`, comments in `scripts/server_contrib/maintenance_window.py`, `scripts/build/config_quick_profile.py` and `tools/uposatha_day.py`, `.gitignore` / `.graphifyignore` entries for `exporter/tpr/output/`. The five extension screenshots in `docs/pics/tpr/` that the docs page no longer uses (`tpr_open_extensions.png`, `tpr_select_dpd.png`, `tpr_downloading.png`, `tpr_extensions.png`, `tpr_dpd_beta.png`). Ask before removing the owner's local TPR db copy (`[tpr] db_path`).

## Not affected

DPD's TPR sutta links (`tools/tpr_codes.json`, `DpdHeadword.has_tpr`, the webapp / GoldenDict / browser-extension links) and the README / newsletter links to TPR.

## How we'll know it's done

- No step in `draft_release.yml` names `tpr`; the YAML parses; the three remaining submodule legs are unchanged.
- `makedict.py` no longer lists the TPR exporter.
- `uv run pytest tests/tools/test_configger.py` passes; ruff and pyright are clean on the touched Python files.
- The TPR docs page no longer tells readers to download DPD from Extensions or to get a beta.
