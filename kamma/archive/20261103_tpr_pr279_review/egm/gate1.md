# Gate 1 — six-lens attack on PR #279

Adaptation: this thread reviews someone else's PR, so Gate 1 attacked the PR itself (with `egm/brief.md` as the hypothesis), not a spec idea.

## Backend log

| Time (IST) | Backend | Event |
|---|---|---|
| 15:14 | pi / deepseek (direct) `deepseek-flash` | smoke probe hung, killed at the 3-minute cap |
| 15:16 | pi / zai `glm-5.3` | smoke probe: every call returned 429. Owner switched the backend |
| 15:18 | pi / azure `deepseek-v4.1-flash` | smoke probe passed (read tool used, 2.4 s) |
| 15:20 | same | 6 reviewers in parallel: 5 stopped on `429 RateLimitReached` (Azure token rate limit), only `cost` finished. Failed logs kept as `raw/gate1_<lens>_try1_429.jsonl` |
| 15:25–15:39 | same | retry (counts as the one allowed retry): the 5 failed lenses one at a time. All 5 finished, 0 errors |

All six lenses ran on their own reviewer. None was paired.

## Raw findings

Final text of every reviewer: `raw/gate1_findings.md`. Event logs: `raw/gate1_<lens>.jsonl`.
Lens keys: C = contrarian/YAGNI, Co = cost, U = UX, M = migration, S = SRE, D = tech debt, E = Elephant (my own checks, see `brief.md`).

## Disposition (deduplicated: 30 findings)

| # | Finding | Sev | From | Decision | How checked |
|---|---|---|---|---|---|
| 1 | `gh release upload --clobber` deletes the live asset before it uploads the new one: readers get a 404 during the upload, and the file stays missing if the upload fails | Blocker | D M U S E | Accept | cli/cli `pkg/cmd/release/shared/upload.go` `uploadWithDelete`: `deleteAsset` runs first |
| 2 | `find -mmin -180` lets files from the checkout through, so the committed `dpd_beta.zip` is re-uploaded every release day | Major | C Co D M S U E | Accept | run 40273393873: checkout done 05:20, TPR step 06:12 (52 min) |
| 3 | The beta entry now points at the release, but nothing uploads a beta: CI never builds one, and local beta builds do not upload | Major | M E | Accept | `configger.py:78` `make_beta` default `no`; `github_release` profile does not set it |
| 4 | `tpr_exporter.py` writes `Legacy (build 128 or lower)` into `download_list.json` too, the list only old builds read | Major | D M U E | Accept. The effect on old builds' screens is unverified | upstream `download_list.json` has `Dictionaries` / `Other Beta` |
| 5 | The upload is gated on `steps.tpr` only; a package build failure is never surfaced, and a legacy failure blocks a good package | Major | C D M S U | Accept | PR `draft_release.yml` upload `if:` and `OUT_TPR` |
| 6 | An upload failure gives no `::error::` | Major→Nit | C S | Accept as Nit | the collect step does print `::warning:: … not collected` when `OUT_TPR` is failure |
| 7 | `_update_download_list` silently skips a missing file or entry; `tpr_package` then prints `OK` | Major→Nit | S U C | Accept as Nit | `tpr_exporter.py:327-344`, PR `tpr_package.py` `update_download_list` |
| 8 | The list updater can only replace an entry, never add one | Nit | C U | Accept | same function. The entries exist upstream today only because they were added by hand |
| 9 | `release_zips/dpd.zip` (23.5 MB) is still committed to tpr_downloads git every month, as well as uploaded | Major | Co D E | Accept. This predates the PR, but the PR makes it redundant | collect step stages `.` for tpr_downloads |
| 10 | The package rebuilds the headword HTML the legacy exporter just built in the same job | Nit | Co C | Accept as Nit | about 2 min. The "toward the 6-hour cap" claim was rejected: the job takes about 66 min, and there are 89,774 headwords, not 460k |
| 11 | The package has no `remove` phase | Major | Co D M U | Escalate to the author | TPR's own README recommends one; what TPR does on uninstall is unknown |
| 12 | The package is 411 MB unzipped; TPR keeps it as `packages/dpd.db` and also copies its rows into the main database | Major | Co E | Accept, and ask the author | central directory of the live `dpd.pkg.zip`: uncompressed 411,168,768 bytes |
| 13 | Myanmar: `github.com/.../releases/download` redirects to `release-assets.githubusercontent.com`; the jsDelivr switch was made because a GitHub file host was blocked there | Blocker (claimed) | C M U E | Escalate (unverified) | redirect seen with `curl -I`. The author says TPR translations already come from releases |
| 14 | Is a second format needed? Does TPR 129 still read `.sql`? If so, the outage fix and the package are separate changes | Major | C | Escalate to the author | TPR README says "use a package instead", but does not say `.sql` was dropped |
| 15 | A 129+ reader who installs the legacy zip after the package gets old base tables, package-era extras, all `has_*` flags 0, and the package re-applies after the next app update | Major | M | Escalate (TPR behaviour) | legacy SQL inserts 4 columns only (`tpr_updater`) |
| 16 | `meta.version` is `yyyymmdd`: a same-day rebuild never reaches devices | Nit | D M | Accept | TPR README: "a higher one is applied over a lower one" |
| 17 | `has_word_family` is always 0 | Major (claimed) | C U | Reject | the current legacy schema has the same column, also 0; no word-family table has ever shipped |
| 18 | Duck-typed `GlobalVars` passed into `tpr_exporter` behind three `type: ignore`; `tpr._update_download_list` and `tpr.DpdRoot` reached through the other module | Major | D U | Accept | PR `tpr_package.py` `main`, `make_i2h` |
| 19 | The table schemas are duplicated and must match the TPR app, with no tests | Major | D E | Accept | no `tests/exporter/tpr/test_tpr_package.py` |
| 20 | `ruff format --check` fails on both PR Python files; the pre-commit hook would reject them | Major | D E | Accept | run locally: 24 changed lines |
| 21 | The `make_i2h` docstring says it equals `i2h.tsv`, but it adds 13,087 sutta-code keys | Nit | D U E | Accept | live db: 459,013 vs 445,926 keys; extras like `AN2.189` come from `suttas_to_lookup.py` |
| 22 | `RELEASE_URL` duplicates `_tpr_download_url` and the `dpd` tag in the workflow | Nit | C D | Accept | read |
| 23 | `compresslevel=9` costs CPU for little gain | Nit | Co | Accept as Nit | memory note: level 9→6 was a 3.4× speed-up elsewhere |
| 24 | Peak memory risk on the runner | Nit | Co | Reject | same `.all()` pattern as the legacy exporter; the counts quoted were wrong |
| 25 | The `dpd` release may not exist | Blocker (claimed) | C | Reject | `gh release view dpd`: it exists, with all three assets |
| 26 | `freq` primary key on `lemma_1` could collide | Nit | D | Reject | `lemma_1` is unique in `dpd_headwords` |
| 27 | An empty upload is reported as success while the list is still pushed | Blocker (claimed) | S | Reject | the exporter rewrites the list only right after it writes the zip, so a changed list always has a fresh zip beside it |
| 28 | `OUT_TPR` lets `skipped` / `cancelled` through | Major (claimed) | S | Reject | the upload is skipped only when `tpr` failed (then `OUT_TPR` is failure anyway) or on a dry run (intended) |
| 29 | A dry run builds a package it never uses | Nit | U | Reject | intended: it tests the step. The runner is thrown away |
| 30 | `report()` prints counts only, not the version, size or list entry | Nit | S | Accept | read |

Totals: 30 findings. 19 accepted, 4 escalated, 7 rejected.
