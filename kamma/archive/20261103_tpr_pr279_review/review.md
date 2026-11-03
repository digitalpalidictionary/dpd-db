# Review — PR #279 "TPR: all-in-one DPD package, and both TPR zips served from a release"

## Outcome (2026-11-03)

The owner went further than this review's recommendation: the whole TPR build moves to the author, and DPD switches off its TPR export once the author's build works. The reply that was actually posted (owner's account, PR left open) is https://github.com/digitalpalidictionary/dpd-db/pull/279#issuecomment-6601345237. It supersedes the "Smallest DPD-side change" section below. Next step and removal scope: `spec.md`.

- PR: https://github.com/digitalpalidictionary/dpd-db/pull/279 (bksubhuti, branch `tpr-package`, 4 files, +469 −9)
- Reviewed 2026-11-03. Goldfish record: `egm/gate1.md` (6 reviewers, 30 findings: 19 accepted, 4 escalated, 7 rejected).
- Nothing has been posted to GitHub.

## Verdict

Do not merge as it stands. The outage it fixes is real: `dpd.zip` is 23.5 MB, and jsDelivr refuses files over 20 MB. The package itself works: the author tested it on macOS and Android. But almost all the risk is in one part: DPD's release workflow uploading into the author's repo. And the package does not need DPD's repo at all. It reads only `dpd.db`, which every DPD release already ships as `dpd.db.tar.xz`. The author built the October package exactly that way.

Recommendation: the author builds and uploads the package from his own repo, on a trigger DPD already provides (below). DPD keeps only a small change for the legacy zip, or none.

## Strengths

- It fixes a real outage for every TPR reader.
- `tpr_package.py` builds everything from `dpd.db` alone, with parameterised inserts. The old exporter builds SQL text by string concatenation.
- The install is one transaction on the device, and re-installing gives the same result (tested by the author).
- The new list is pushed only after the upload works, and a dry run builds the package but publishes nothing.
- It needs no new secrets or settings.

## Flaws (most severe first)

1. **Delete before upload.** `gh release upload --clobber` deletes the live file first, then uploads (cli/cli `uploadWithDelete`). During the upload of a 61.5 MB file, every reader gets a 404. If the upload fails, the file stays gone while the live list still points at it.
2. **The "only today's files" filter does not work.** `find -mmin -180` also passes files fresh from the checkout. In the 26 Oct run, the TPR step ran 52 minutes after checkout. So the committed, old `dpd_beta.zip` is uploaded on every release day.
3. **The beta breaks.** CI never builds a beta (`make_beta` is `no` in CI). The beta entry now points at the release, but a local beta build updates the list and not the file.
4. **Old TPR builds get the new heading.** The exporter writes `Legacy (build 128 or lower)` into `download_list.json` too, and only old builds read that list. Whether their screens still show the entry is unverified.
5. **Package failures are invisible.** The upload step checks only the legacy exporter's result. A package build failure leaves the run green, and a legacy failure blocks a good package.
6. **The big zip still goes into git.** `release_zips/dpd.zip` (23.5 MB) is still committed to tpr_downloads every month, as well as uploaded. This predates the PR, but the PR makes the git copy redundant.
7. **Coupling and gates.** `tpr_package.py` passes its own `GlobalVars` into the old exporter's functions with type checks switched off, and calls its private list helper. It has no tests. It fails `ruff format`, so this repo's commit hook rejects it.

Smaller points:

- The `make_i2h` docstring says it matches `i2h.tsv`; it adds 13,087 sutta-code keys (harmless).
- The list updater only replaces entries and never adds them, and it prints `OK` after a silent skip.
- The version is `yyyymmdd`, so a same-day rebuild never reaches devices.
- `RELEASE_URL` is duplicated.
- Zip level 9 is slow for little gain.
- The headword HTML is built twice per run (about 2 min).

## Questions for the author (unverified)

1. **Myanmar.** Release downloads redirect to `release-assets.githubusercontent.com`. The jsDelivr switch was made because a GitHub file host was blocked there. You say TPR's translations already come from releases. Has a reader in Myanmar confirmed that those download?
2. **Phone storage.** The package is 411 MB unzipped (read from the live zip). TPR keeps it as `packages/dpd.db` and also copies the rows into its main database. Is about 800 MB for DPD on a phone acceptable? Could TPR drop the kept file after install, or store it zipped?
3. **Uninstall.** There is no `remove` phase. What does TPR do when a reader removes the package?
4. **Legacy zip on a new build.** If a build-129 reader installs the legacy `dpd.zip` after the package, they get old base tables beside the package's extras, with every button flag at 0. Then the next app update re-applies the package. Should the legacy entry be hidden from 129+?
5. **Does build 129 still read `.sql`?** If yes, the URL fix alone ends the outage, and the package is a separate feature.

## Suggested automation in tpr_downloads

The trigger already exists. On each release day, DPD's push job commits `release_zips/dpd.zip` to tpr_downloads `master`. That job runs after the DPD release is published, so `dpd.db.tar.xz` is already downloadable. A workflow in tpr_downloads that fires on that push can do the rest. It needs no secrets beyond its own `GITHUB_TOKEN`, and a commit made with that token does not start the workflow again.

Sketch (`.github/workflows/dpd_package.yml` in bksubhuti/tpr_downloads; untested):

```yaml
name: DPD package
on:
  push:
    branches: [master]
    paths: [release_zips/dpd.zip, release_zips/dpd_beta.zip]
  workflow_dispatch:
concurrency: { group: dpd-package, cancel-in-progress: false }
permissions: { contents: write }

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      GH_TOKEN: ${{ github.token }}
    steps:
      - uses: actions/checkout@v5

      - name: Latest DPD release
        id: dpd
        run: |
          tag=$(gh release view -R digitalpalidictionary/dpd-db --json tagName -q .tagName)
          echo "tag=$tag" >> "$GITHUB_OUTPUT"
          echo "version=${tag##*.}" >> "$GITHUB_OUTPUT"   # v0.4.20261026 -> 20261026

      - uses: actions/checkout@v5
        with:
          repository: digitalpalidictionary/dpd-db
          ref: ${{ steps.dpd.outputs.tag }}   # the code that made this dpd.db
          path: dpd-db
          submodules: false                   # the package needs none of them

      - uses: astral-sh/setup-uv@v6

      - name: Build the package
        working-directory: dpd-db
        run: |
          gh release download "${{ steps.dpd.outputs.tag }}" -R digitalpalidictionary/dpd-db -p dpd.db.tar.xz
          tar -xJf dpd.db.tar.xz
          uv sync
          uv run python exporter/tpr/tpr_package.py --db dpd.db --version "${{ steps.dpd.outputs.version }}"

      - name: Upload under new names, then point the list at them
        run: |
          set -euo pipefail
          v=${{ steps.dpd.outputs.version }}
          cp dpd-db/exporter/tpr/output/dpd.pkg.zip "dpd_$v.pkg.zip"
          cp release_zips/dpd.zip "dpd_$v.zip"
          # new names, no --clobber: the files the live list points at stay up
          gh release upload dpd "dpd_$v.pkg.zip" "dpd_$v.zip"
          # your own small script: set url, size and release_date of the two entries
          python3 scripts/point_dpd_entries.py "$v"
          git config user.name "github-actions[bot]"
          git config user.email "41898729+github-actions[bot]@users.noreply.github.com"
          git commit -am "DPD $v package"
          git push
          # then delete dpd_*.zip assets older than the last two versions
```

What this fixes, from the flaw list:

- **Flaw 1:** new file names mean nothing live is deleted. The list moves to the new files only after they are up. The `filename` field can stay `dpd.pkg.zip` / `dpd.zip`, because TPR already keeps the URL and the file name apart (the beta entry uses `dpd_beta.zip` as its URL and `dpd.zip` as its file name).
- **Flaws 2, 3, 5:** the workflow uploads exactly the files it just built, and any failure turns that run red in the author's repo.
- **The version:** it comes from the DPD release tag, so it goes up on each release and matches the release.
- **The code version:** the package builder runs from the same DPD tag as the database, so code and data always match.
- **DPD's workflow** does not change.

Caveats to state to the author:

- `tpr_package.py` would still live in DPD's repo, because it imports DPD's models and the `tpr_headword.jinja` template. Either DPD merges only that file, with no workflow change (formatted, with a test), or the author keeps it in tpr_downloads and checks out DPD only for the imports. With the second choice, a DPD model change can break the author's build. That failure shows in the author's repo, which is where it can be fixed.
- DPD's exporter rewrites the `dpd.zip` entry each release (URL and category). Until DPD changes it, the author's workflow must re-set that entry's URL after DPD's push. That is why the workflow runs on DPD's push, not before it.
- The trigger path assumes DPD keeps committing `release_zips/dpd.zip`. If DPD stops (flaw 6), the trigger becomes a daily schedule that compares the latest DPD tag with the last one built.

## Smallest DPD-side change (if the owner wants one)

In `exporter/tpr/tpr_exporter.py`, only:

- `_tpr_download_url` → the release URL, and the suffixes → `/dpd/dpd.zip`, `/dpd/dpd_beta.zip` (the PR's 4 lines).
- No category change, so both lists keep `Dictionaries` / `Other Beta`.

Everything else in the PR (the workflow steps, `tpr_package.py`, the README line) stays out of DPD, or `tpr_package.py` comes in alone after formatting and a test.
