# Brief — review of PR #279 (TPR all-in-one package)

## Request (owner, 2026-11-03)

> check out the new pull request from bksubhuti related to TPR and give me a full review: strengths, weaknesses, flaws. Use pi as goldfish.

Goldfish backend: pi, `--provider azure --model deepseek-v4.1-flash`, read-only tools. DeepSeek (direct) hung on the smoke probe; Z.ai GLM 5.3 returned 429 on every call. Both abandoned on owner instruction.

## The PR

- https://github.com/digitalpalidictionary/dpd-db/pull/279 — "TPR: all-in-one DPD package, and both TPR zips served from a release", author bksubhuti, branch `bksubhuti:tpr-package`, base `main`. 4 files, +469 −9.
- Copies of the PR files (PR versions): `egm/pr279/tpr_package.py.txt` (new), `egm/pr279/tpr_exporter.py.txt`, `egm/pr279/draft_release.yml`, full diff `egm/pr279/pr279.diff`.
- Current `main` versions: `exporter/tpr/tpr_exporter.py`, `.github/workflows/draft_release.yml`.
- TPR package format (from bksubhuti/tipitaka-pali-reader): `egm/pr279/tpr_ext_readme.md`.
- Upstream download lists at bksubhuti/tpr_downloads@master today: `egm/pr279/up_download_list.json`, `egm/pr279/up_download_list_2.json`.

What it does: jsDelivr refuses files over 20 MB, and `dpd.zip` is now 23.5 MB, so TPR readers get a 49-byte error. The PR uploads TPR zips to a GitHub release (`dpd` tag of bksubhuti/tpr_downloads) and points the download lists there. It adds `tpr_package.py`, which builds `dpd.pkg.zip` (61.5 MB), a SQLite "extension package" for TPR build 129+ holding the dictionary plus the extras (inflections, root/compound families, frequency, grammar). The legacy `dpd.zip` stays for build 128 and lower.

## Facts verified by the Elephant (claims to re-check, not facts)

1. `gh release upload --clobber` deletes the existing asset first, then uploads (cli/cli `pkg/cmd/release/shared/upload.go`, `uploadWithDelete`). A failed upload leaves no asset at the URL the live list points at.
2. The upload step picks files with `find -mmin -180`. In the 2026-10-26 release run, checkout finished 05:20 and the TPR exporter ran 06:12. Files that come from the checkout (the committed `release_zips/dpd_beta.zip`) are under 180 minutes old, so they pass the filter although this run did not make them.
3. CI config profile `github_release` leaves `[tpr] make_beta` at the default `no`. So CI never builds the beta. Beta builds happen on the maintainer's machine (local `dpd_beta.zip` dated 3 Oct 2026). After the PR, the beta list entry points at the release, but nothing uploads a locally built beta to it.
4. The collect step stages `resources/tpr_downloads` with `git add -- .`. So `release_zips/dpd.zip` (23.5 MB) is still committed to tpr_downloads git every month, as well as uploaded to the release.
5. The upstream lists already point at the `dpd` release (bksubhuti edited them by hand). `download_list.json` (read by old TPR builds) still has categories `Dictionaries` and `Other Beta`. The PR's `tpr_exporter.py` writes `Legacy (build 128 or lower)` into BOTH lists.
6. `make_i2h` reads `lookup.headwords`. That column holds 459,013 keys; the db pipeline's `i2h.tsv` holds 445,926. The 13,087 extra keys are sutta codes (`AN2.189`, `SN24.17`, …) that `db/suttas/suttas_to_lookup.py` adds. The docstring claim "the same as the i2h.tsv" is false.
7. `ruff check` and `pyright` pass on both PR Python files. `ruff format --check` fails on both (24 changed lines). The pre-commit gate would reject the commit.
8. No tests are added.
9. The package has no `remove` phase. TPR's format README says a package keeps its file on the device (`packages/<id>.db`) and reapplies it after app updates.
10. The upload step runs inside the build job, before the push job. The push job is the one that publishes the new list.

## Anchored hypothesis

PR #279 fixes a real outage (TPR readers cannot download DPD) and adds the all-in-one package TPR 129+ needs. The package builder is sound in direction, but the release-upload step has gaps: it deletes before it uploads, its file-age filter lets old checkout files through, and local beta builds no longer reach readers. The thread's job is a written review plus the list of changes needed before merge, not a rewrite.
