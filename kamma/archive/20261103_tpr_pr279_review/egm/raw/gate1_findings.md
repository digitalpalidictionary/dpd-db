===== gate1_contrarian.jsonl (tool calls: 26, error: None)
## Review: PR #279 (contrarian / YAGNI)

**Blocker — the new URL may be blocked in the target market.**
`tpr_exporter.py:318-320` (PR) replaces jsDelivr with `https://github.com/bksubhuti/tpr_downloads/releases/download/dpd/...`. Current main (`exporter/tpr/tpr_exporter.py:318-320`) states jsDelivr was chosen precisely because `raw.githubusercontent.com / github.com/.../raw/...` are **blocked in Myanmar** — the users this outage is about. `github.com/.../releases/download/` is still github.com. Nothing in the PR verifies it is reachable there.
*Fix:* confirm reachability from Myanmar before merge; if blocked, the only viable fix is keeping artifacts under 20 MB (e.g. split `dpd.sql`) on the CDN, not moving to github.com.

**Blocker — the release is assumed to pre-exist.**
`draft_release.yml:389` only does `gh release upload dpd ... --clobber`; there is no `gh release create`. If tag `dpd` is absent/renamed, upload fails, `continue-on-error: true` keeps the job green, and the outage continues.
*Fix:* `gh release view dpd || gh release create dpd`, and don't swallow the failure.

**Major — upload is gated on the wrong exporter.**
`draft_release.yml:372` conditions on `steps.tpr.outcome`, ignoring `steps.tpr_package.outcome`. A failing legacy exporter blocks upload of a successfully built package; a failing package build is invisible.
*Fix:* gate/upload each artifact independently.

**Major — upload failure is silent.**
`draft_release.yml:370-389`: `continue-on-error` plus no `::error::`. The list push is correctly suppressed (`OUT_TPR`, line 404), so the failure mode is "stale links, green run, nobody paged."
*Fix:* emit an `::error::`/fail the step.

**Major — the download-list writer never inserts.**
`tpr_package.py:366` delegates to `_update_download_list`, which replaces at `index` only and `pr.red(...skipping)` when not found (`tpr_exporter.py:334-343`). On a fresh/renamed `download_list_2.json` the package is silently never published. The docstring claims the entry is "moved"; it is only overwritten in place.
*Fix:* append the entry when absent.

**YAGNI — is a second format needed at all?**
`tpr_ext_readme.md` says "Use a package **instead of** a `.sql` extension" — it never says TPR 129 dropped `.sql`. The PR's `category: "Legacy (build 128 or lower)"` labels are self-imposed. The live lists already ship `dpd.zip` (23.5 MB) + `dpd__extras.zip` (11.4 MB) via `up_download_list.json`, both under the CDN limit. The new package is **61.5 MB** (`up_download_list_2.json:7`) — 2.6× the bytes for users who only need the 23.5 MB dictionary moved. The outage fix is the URL move; the package is an unrelated feature and could ship separately.
*Fix:* get TPR to state whether 129 still reads `.sql`; if yes, ship only the moved legacy zips.

**YAGNI — rebuilds data an existing pass just produced.**
`tpr_package.py:107 make_i2h` re-derives `i2h` though the sibling `tpr_exporter` in the *same job* already writes `i2h.tsv` (`tools/paths.py:298`). `mobile_exporter.py` already extracts `family_root/family_compound/freq_data` (lines 47/76/324). The package duplicates both.
*Fix:* read the sibling TSVs / share the extractor.

**Major (correctness) — Word Family flag is dead.**
`headword_rows` hard-codes column 8 (`has_word_family`) to `0` (`tpr_package.py:45`, `EXTRA_TABLES` has no word-family table). If 129 renders that button, it will never light.
*Fix:* populate it or drop the column from the advertised schema.

**Nit — two URL sources of truth.** `RELEASE_URL` (`tpr_package.py:38`) duplicates `_tpr_download_url`; only the constant is updated by hand.

**Nit — `find "$f" -mmin -180`** (`draft_release.yml:383`) is a wall-clock heuristic; a slow/clock-skewed runner silently drops freshly built artifacts from the upload set. Track produced files explicitly instead.
===== gate1_cost.jsonl (tool calls: 29, error: 429: {"code":"RateLimitReached","message":"Your requests to DeepSeek-V4.1-Flash for DeepSeek-V4.1-Flash in eastus2 have exceeded token rate limit.","details":"Your requests to DeepSeek-V4.1-Flash for )
## Cost / quota / resource review — PR #279

**1. Blocker — tpr_downloads git repo keeps growing ~23.5 MB/month**
`exporter/tpr/tpr_exporter.py:381` writes the release zip to `release_zips/dpd.zip` (`tools/paths.py:651`), which is a *tracked* file; the collect step stages the whole submodule with `git add -- "$stage"` where stage is `.` for tpr_downloads (`draft_release.yml:415,439`), and the checkout at `resources/tpr_downloads/.gitignore` does not exclude `release_zips/`. So every release commits a fresh 23.5 MB binary (plus `dpd_beta.zip` when built locally).
Failure: after ~3–4 years the submodule exceeds GitHub's 1 GB / repo-size guidance; every clone/push of tpr_downloads and every DPD release checkout gets slower, and the object store only grows (no GC). This is the exact storage problem the PR set out to avoid, left in place.
Fix: in tpr_downloads, `git rm --cached release_zips/dpd.zip release_zips/dpd_beta.zip`, add both to `.gitignore`; rely solely on the release assets. Do not stage `release_zips`.

**2. Major — stale committed zips are re-uploaded every run**
`draft_release.yml:376-389` selects files with `find "$f" -mmin -180`. Checkout stamps every file with the checkout time, so the committed `release_zips/dpd.zip`/`dpd_beta.zip` pass even on a run that built nothing.
Failure: on a day the exporter returns success without reaching `copy_zip_to_tpr_downloads` (e.g. no uposatha/beta disabled), the old committed zip is uploaded over the release asset, and the new download list points readers at stale data — while ~50–108 MB is pushed to GitHub each run.
Fix: drop the mtime heuristic; upload only paths the current run actually wrote (have the exporter emit them, or compare a hash/version), and guard the step on `steps.tpr_package`/`tpr` having produced files.

**3. Major — the package re-does the exporter's whole build inside the same job**
`tpr_package.py:403-405` calls `generate_tpr_data`, `generate_deconstructor_data`, `add_spelling_mistakes` again; `draft_release.yml:346` already ran `tpr_exporter.py`, which does the same work, including rendering HTML for ~460k headwords through Jinja.
Failure: the heaviest CPU stage (single-threaded Jinja rendering, full `Lookup` scans) runs twice per release, roughly doubling that stage's CI minutes and pushing a long job toward the 6-hour cap. The duplicate `dpd.pkg.db` build also runs even if `tpr_exporter` failed, yet the upload is skipped (`draft_release.yml:371`, condition `steps.tpr.outcome == 'success'`) — pure waste.
Fix: build both artifacts from one in-memory pass (shared module), or make tpr_package consume the exporter's staged TSVs/DB instead of recomputing.

**4. Major — package has no `remove` phase; phone storage never reclaimed**
`tpr_package.py:248-266` emits only `"install"` steps; `tpr_ext_readme.md` says "A remove phase is usually those same deletes plus the `reindex`." Combined with the 61.5 MB zip and "it is kept on the device", a user can never uninstall it and the old copy survives app updates/reinstalls.
Fix: add the `remove` phase (delete the package-owned rows + reindex) so TPR can offer uninstall.

**5. Major — install cost on a phone**
`commands()` copies every row of 10 tables (dpd ~460k, inflections ~460k, word-split, grammar, six extras, freq) in one `INSERT OR REPLACE` transaction, then builds six indexes. With the 61.5 MB download plus the kept `.db` plus the installed copy, a low-end device needs a large free-storage margin; a mid-install storage exhaustion aborts the transaction after the download is already spent, and install can take minutes.
Fix: document the required free space prominently; trim unused payload (`has_word_family` is always 0 at `tpr_package.py:236`).

**6. Nit — `compresslevel=9`**
`tpr_package.py:325` deflates a large SQLite single-threaded at level 9 for marginal size gain over 6; adds minutes of runner CPU per release.

**7. Nit — peak memory**
`tpr_package.py:92,116,153` load the full `DpdHeadword` table and two full `Lookup` scans into memory alongside `tpr_data_list` and the extra row lists. Not clearly worse than the existing exporter, but headroom on a 7 GB runner is thin; stream rows instead of `.all()` if the exporter is refactored.

Release-asset size is fine: 61.5 MB is far under GitHub's 2 GiB per-asset limit.
===== gate1_debt.jsonl (tool calls: 18, error: None)
# PR #279 review — long-term maintenance lens

## Major

**1. Release upload deletes before it replaces (outage risk).** `gh release upload ... --clobber` (draft_release.yml:389) removes the existing asset before writing the new one. The live `download_list_2.json` already points at `.../dpd/dpd.zip` (up_download_list_2.json:70). A failed or interrupted upload leaves every current TPR reader with a 404 until a rerun. Fix: upload to a versioned filename (e.g. `dpd_2026-11.zip`), update the list only after success, never clobber the asset an already-published list references.

**2. The age filter uploads stale checkout files.** `find "$f" -mmin -180` (draft_release.yml:383) only tests mtime, and checkout refreshes mtime on every tracked file. `resources/tpr_downloads/release_zips/dpd_beta.zip` is committed, so each release re-uploads an old, locally built beta as `dpd_beta.zip`, while `tpr_exporter` stamps it with today's `release_date` (tpr_exporter.py:400-415). CI never builds beta (`[tpr] make_beta` default `no`). Readers silently get stale content labelled current. Fix: drop mtime; upload only files the run actually produced (guard on step outcome / explicit manifest), or build beta in CI.

**3. Upload gates on the wrong step.** Condition is `steps.tpr.outcome == 'success'` (draft_release.yml:372); `steps.tpr_package` is ignored, and `OUT_TPR` (line 404) also never sees `tpr_package`. A package-builder failure can therefore let the workflow publish a `download_list_2.json` whose `dpd.pkg.zip` entry has no asset. Fix: make the upload and the collect gate depend on both exporters.

**4. Duck-typed GlobalVars bridge.** `tpr_package.GlobalVars` (tpr_package.py:85) is passed to `tpr_exporter` functions behind three `# type: ignore[arg-type]` (tpr_package.py:403-405). It works only because those functions happen to touch `db_session`, `dpd_db`, `all_headwords_clean`, `deconstructor_data_list`. Any future use of `tpr_df`/`i2h_df` breaks the package build at runtime with no type error. Fix: extract the shared generators into a module with a `Protocol`/ABC, or pass explicit arguments; delete the ignores.

**5. Duplicated, untested schema.** `BASE_TABLES["dpd"]` (tpr_package.py:42-47) duplicates the literal `CREATE TABLE "dpd"` in tpr_exporter.py:235-245; `EXTRA_TABLES` (tpr_package.py:61-77) must match the TPR app forever, with no contract test. A one-sided edit produces a package that installs to the wrong shape. Fix: single schema source + a test enumerating columns and `commands()` output.

**6. No tests for the new exporter.** `tests/exporter/tpr/test_tpr_exporter.py` mirrors the module; nothing covers `tpr_package.py` (`commands`, `headword_rows`, `write_package`, meta/format, `_update_download_list` reuse). Fix: in-memory package test asserting meta `format`, table columns, and copy targets.

**7. Private helper used cross-module.** `tpr._update_download_list` (tpr_package.py:378) and `tpr.DpdRoot` (line 122) reach into an underscore-private API of an exporter. Fix: promote to a shared public module.

**8. Format gate fails.** `.pre-commit-config.yaml` runs `ruff format`; the PR is unformatted (`ruff format --check` fails per brief; e.g. overlong lines tpr_package.py:253). Running the hook rewrites the commit. Fix: format + lint before merge.

**9. Category rename leaks to old clients.** tpr_exporter.py:390,408 writes `"Legacy (build 128 or lower)"` into BOTH lists, but `download_list.json` is read by old builds that only know `Dictionaries`/`Other Beta` (up_download_list.json:112,254). Fix: keep legacy categories in `download_list.json`; new category only in list_2.

**10. No `remove` phase, date-only version.** `commands()` (tpr_package.py:248) emits install steps only; the format README says removal normally deletes owned rows. Removal leaves DPD rows on-device, and a same-day rebuild gets the same `yyyymmdd` version, so devices won't reapply. Fix: add `remove` + reindex; bump version on content change.

## Nit

- `make_i2h` docstring claims equality with `i2h.tsv`; it reads `lookup.headwords`, adding sutta codes (tpr_package.py:107-119). Correct or reword.
- `RELEASE_URL` (tpr_package.py:38) duplicates tpr_exporter.py:321 and the `dpd` tag in draft_release.yml:389 — one constant.
- `find -mmin`, `git add -- .` on `resources/tpr_downloads` re-commits the 23.5 MB `dpd.zip` into git monthly (draft_release.yml collect step, stage `.`), duplicating the release asset and bloating history.
- `freq` PK is `headword` = `lemma_1`; duplicate lemmas would raise `IntegrityError` on `executemany` (tpr_package.py:70).
===== gate1_migration.jsonl (tool calls: 19, error: None)
## PR #279 review — Migration & backward-compatibility lens

**1. Blocker — `--clobber` deletes the live asset before upload.** `draft_release.yml:389` runs `gh release upload dpd ... --clobber`; the live lists already point at exactly those URLs (`up_download_list_2.json:5` `.../release/download/dpd/dpd.pkg.zip`, `up_download_list.json` `.../dpd/dpd.zip`). A failed/interrupted upload after the delete leaves the advertised file gone. Build 128 readers lose the working `dpd.zip`; build 129+ lose the package. Fix: upload to a new tag/filename, verify size/sha256, then update the list; never clobber the asset the list currently references.

**2. Blocker — beta list points at an asset nothing uploads.** `draft_release.yml:372,379-389` only uploads what passes `-mmin -180`, and `make_beta` defaults `no` (`tpr_exporter.py` main). Yet the beta entry (`up_download_list_2.json`, `tpr_exporter.py:409`) now points at `.../dpd/dpd_beta.zip`. Build 128 beta users get 404, or a stale committed beta that happens to pass the age filter. Fix: build/upload beta in the release, or drop the beta entry until an asset exists.

**3. Major — legacy `download_list.json` categories renamed, mirror removed.** `tpr_exporter.py:390,408` write `"Legacy (build 128 or lower)"` into **both** lists, replacing `"Dictionaries"`/`"Other Beta"`. Old TPR builds read `download_list.json` and only surface categories they know, so the DPD and Beta entries disappear from their UI. The URL also moved from jsDelivr to `github.com/...` (`tpr_exporter.py:318-321`), removing the mirror the old code comment said was needed because github is blocked in Myanmar. Fix: keep old category names and a reachable mirror in `download_list.json`; use the new category only in list 2.

**4. Major — no `remove` phase.** `tpr_package.py:249-267` emits only `phase='install'`; `tpr_ext_readme.md` says a package should carry a `remove` phase (same deletes plus reindex). Uninstalling the package cannot clear the base rows it deleted/refilled or the extra tables it created. Fix: add a matching `remove` phase.

**5. Major — legacy zip installed after the package leaves mixed state.** The legacy installer deletes only `dpd`, `dpd_inflections_to_headwords`, `dpd_word_split` (`tpr_exporter.py` `tpr_updater`; `copy_to_sqlite_db` creates only those three). It never touches `dpd_grammar` or the extras, which `tpr_package.py BASE_TABLES`/`EXTRA_TABLES` own and drops/recreates. A build-129 user who picks the "Legacy" entry gets old base data, package-era grammar and extras, all `has_*` flags 0 — and the package is re-applied after the next app update, silently reverting the choice. Fix: hide the legacy entry from build 129+, or have it explicitly drop package tables.

**6. Major — version is only `yyyymmdd`.** `tpr_package.py:280,399`. The format applies a package only when `version` is *higher* (`tpr_ext_readme.md`). Two builds the same day, or a rebuild to fix data, share a version and never reach devices already on it. Fix: monotonic build number/time or content hash.

**7. Nit — upload gating ignores the package exporter.** `draft_release.yml:372` conditions on `steps.tpr.outcome` only. If the legacy exporter fails but the package succeeds, nothing uploads; if the package fails, the legacy upload proceeds. Add `steps.tpr_package.outcome` to the condition.

**8. Nit — age filter is not "only what this run made".** `draft_release.yml:382-383`: checkout stamps committed `release_zips/*.zip` with the checkout time, so they pass `-mmin -180`. Uploads a stale committed zip under a fresh-list run. Fix: build into a clean output dir and test presence there, not mtime.
===== gate1_sre.jsonl (tool calls: 21, error: None)
Findings — PR #279 observability/SRE (read-only; nothing changed)

**Blocker — an empty upload is reported as success, but the list is still pushed.** `draft_release.yml:383-389`: when the file-age filter selects nothing, the step prints `Nothing made for TPR today` and `exit 0`. Meanwhile `tpr_exporter.py:398,417` may already have rewritten the list to `/dpd/dpd.zip`. `OUT_TPR` (`:404`) then resolves to `steps.tpr.outcome` = success, so `collect_submodules` stages `tpr_downloads` and `push-submodules` pushes a list pointing at an asset this run never uploaded. Reader sees 404/stale DPD; logs show a green step and a plain echo. Fix: treat "expected file(s) for today's exporter run absent" as failure or `::warning::`, set a step output, and gate `OUT_TPR`/push on that output; add a post-upload existence/size check against the URL.

**Major — `tpr_package` outcome is never consulted.** `draft_release.yml:372` gates only on `steps.tpr.outcome`, and `:404` ignores `tpr_package`; both are `continue-on-error`. If the 61.5 MB package build dies (OOM, sqlite error), the run stays green, the upload leg proceeds with `dpd.zip`, and no error is surfaced. Fix: join `steps.tpr_package.outcome` into the condition and `OUT_TPR`, and emit `::error::` on failure.

**Major — file-age filter is provenance-blind, so stale checkout files pass as "made this run".** `draft_release.yml:383-384` accepts anything with mtime < 180 min. Committed `release_zips/dpd_beta.zip` (local 3 Oct build) is re-checked-out at run start, so it always passes, while CI never builds beta (profile default `no`). `gh release upload --clobber` re-uploads stale content and the step succeeds. Logs list neither the selected files nor their mtimes/hashes, so "new vs. last month's" is undebuggable. Fix: derive selection from VCS state (skip files unchanged vs HEAD) or explicit build outputs, and echo `ls -l` + sha256 per file plus `skipped: older than 180m`.

**Major — silent skips return success in `_update_download_list`.** `tpr_exporter.py:327-329` (missing list) and `:342-344` (no entry ending in `url_suffix`) only `pr.red(...)`; `main` then `pr.yes(version)` (`:417`) and exits 0. Same pattern in `tpr_package.py:355-356` (`pr.no`, `return`) followed by `pr.yes("OK")` (`:367`). Since the suffix changed from `release_zips/dpd.zip` to `/dpd/dpd.zip`, any un-migrated list entry silently won't match. Result: step green, list unchanged, no outcome to block the push. Fix: raise/exit nonzero or emit `::error::`, or return a status the caller aggregates.

**Major — `OUT_TPR` only treats the literal `'failure'` as bad.** `draft_release.yml:404`: `steps.tpr_upload.outcome == 'failure' && 'failure' || steps.tpr.outcome`. Outcomes `skipped`/`cancelled` fall through to `tpr.outcome`, so the `tpr_downloads` tar is collected and pushed although the upload leg never ran (e.g. a cancelled step on a real release). Fix: require `steps.tpr_upload.outcome == 'success'` explicitly.

**Nit — `report()` (`tpr_package.py:331-346`) isn't actionable and runs before the list update.** It prints table counts only; no meta `version`, zip path/size, or resulting list entry, so correlating a build to the published entry means scrolling. A clean report can precede a silent list-update skip (`:355-367`). Fix: include version/size/final entry and append to `$GITHUB_STEP_SUMMARY`.

**Nit — no record of what `gh release upload` actually uploaded.** `draft_release.yml:389` has no `gh release view`/HEAD confirmation; with delete-before-upload a mid-failure leaves no asset. Echo the chosen file list and assert asset presence/size afterward.
===== gate1_ux.jsonl (tool calls: 11, error: None)
Findings below; file references are to the PR copies under `egm/pr279/` unless noted.

**1. Blocker — legacy list loses its DPD category.** `tpr_exporter.py:390,408` write `"category": "Legacy (build 128 or lower)"` into *both* lists (`:396,414`). The live old list has DPD under `"Dictionaries"` (`up_download_list.json`, DPD entry). Next release run rewrites builds ≤128's own list to a heading their UI may not know, hiding DPD/dpd_beta from the users the PR rescues. Fix: new category only in `download_list_2.json`; leave the legacy list's `Dictionaries`/`Other Beta` untouched.

**2. Blocker — `--clobber` deletes before uploading.** `draft_release.yml:389`. Uploading the 61.5 MB `dpd.pkg.zip` deletes the live asset first; if the upload fails, the URL the already-live list points at 404s for Myanmar users. Fix: upload under a temp name, verify size, then swap; or add-before-delete via `gh api`.

**3. Major — false "OK" on list update.** `tpr_package.py:366-367` calls `tpr._update_download_list`, which merely `pr.red`s and returns on a missing file/entry (`tpr_exporter.py:331-344`), then unconditionally prints `OK`. A clean checkout without the hand-added entry builds and uploads the package but never lists it, while logging success. Fix: return/raise on failure.

**4. Major — updater cannot add entries.** `tpr_package.py:366`, `tpr_exporter.py:337-344` only replace an existing URL suffix. The package entry exists upstream solely because it was hand-edited; on a fresh `tpr_downloads` it is skipped forever. Fix: append when no match.

**5. Major — age filter is opaque and uploads stale files.** `draft_release.yml:383` `find -mmin -180` treats any freshly checked-out file as "made this run"; the committed `release_zips/dpd_beta.zip` passes even though config leaves `make_beta=no`, so CI never rebuilds beta but republishes whatever is committed. Fix: list explicit expected outputs; gate beta on the beta step.

**6. Major — package failure invisible.** The upload condition keys on `steps.tpr.outcome`, not `steps.tpr_package.outcome` (`draft_release.yml:372`), and both steps are `continue-on-error: true` (`:357,373`). A package build failure leaves the run green and build-129 users with no package. Fix: include `steps.tpr_package.outcome`; emit `::error::`.

**7. Major — Myanmar reachability unverified.** The diff replaces jsdelivr, explicitly documented as not blocked in Myanmar (`main` `tpr_exporter.py:319-320`), with `github.com/.../releases/download` (PR `:318-322`). If release downloads are blocked, the outage persists. Fix: verify from-country or document a fallback.

**8. Major — no `remove` phase.** `tpr_package.py:commands()` emits only `install`; `tpr_ext_readme.md` says a `remove` phase is the same deletes plus reindex. Uninstalling/disabling the package leaves stale tables. Fix: add the remove phase.

**9. Nit — docstring wrong.** `tpr_package.py:110` claims "the same as the i2h.tsv"; the lookup column also carries sutta-code keys added by `suttas_to_lookup.py`, so the package i2h differs.

**10. Nit — brittle coupling / dead column.** `tpr_package.py:400-404` calls tpr_exporter internals through `GlobalVars` with `type: ignore[arg-type]`; `has_word_family` is hardcoded `0` (`:45`, `headword_rows`). No tests added; `ruff format --check` reportedly fails.

**11. Nit — dry run builds a 61.5 MB artifact it never uses** (`draft_release.yml:361-362`), then leaves it in the workspace. Fix: skip or clean up.
