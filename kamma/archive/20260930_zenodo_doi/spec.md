# Spec: Zenodo DOI in every citation, automatically

## GitHub issue
None — follow-up to the archived thread `kamma/archive/20260906_citations/`
(read its `spec.md`, `plan.md`, `review.md` and `handoff_20260926.md` first).

## Overview

The citations thread (2026-09-06) made DPD citable and planned for Zenodo to add a DOI.
The user has since connected Zenodo to GitHub and published the 26 September release.
Zenodo archived it. But the DOI never reaches any citation, and nothing in the current
design would ever make it do so. This thread makes the DOI appear in every citation
surface, on every build, with no monthly action.

It also makes the Zenodo record itself carry the correct author name and type.

## Established facts (verified 2026-09-30, not assumed)

- **Zenodo has archived the release.** Record `22979414`, version `v0.4.20260926`,
  created 2026-09-26. Concept DOI **`10.5281/zenodo.22979413`**, version DOI
  `10.5281/zenodo.22979414`. `https://doi.org/10.5281/zenodo.22979413` returns HTTP 302
  to `https://zenodo.org/doi/10.5281/zenodo.22979413`. Checked with `curl` against the
  Zenodo API and doi.org.
- **The concept DOI is permanent.** It always resolves to the newest archived release;
  each release gets its own version DOI underneath it. It changes only if the repo is
  disconnected and reconnected on Zenodo.
- **The DOI lookup in `tools/version.py` can never find it.** `fetch_zenodo_doi()`
  queries `q="digitalpalidictionary/dpd-db"`. Run live on 2026-09-30 it returns HTTP 200
  with `total: 0`. Zenodo's free-text search does not index `related_identifiers`. The
  quoted full GitHub URL also returns 0. Only a field query on the exact tag URL
  (`related.identifier:"…/tree/v0.4.20260926"`) finds it.
- **Even a working lookup would not reach the shipped files.** `ensure_doi()` skips the
  lookup when `CI` is set, because `config.ini` is gitignored. `draft_release.yml` runs
  `tools/version.py` in CI and builds `dpd.db`, GoldenDict, the PDF and the mobile db
  there. `scripts/build/config_github_release.py` sets no `doi`. So the released
  `db_info.citation`, the GoldenDict `cite` entry, the PDF front matter and the app's
  How to Cite card would all ship without the DOI. Only the two locally generated
  tracked files (`CITATION.cff`, `docs/how_to_cite.md`) could carry it.
- **Local `config.ini` has no `[version] doi` key** (only `version = v0.4.20260930`).
- **Every consumer of the DOI**, from `rg -n "get_doi|make_citation"` across the repo
  (excluding `archive/`, `kamma/`, `graphify-out/`):
  - `tools/version.py` — `get_doi`, `ensure_doi`, `fetch_zenodo_doi`, `_hit_is_dpd`,
    `main()`
  - `tools/docs_update_how_to_cite.py:119` — `make_how_to_cite_md(version, get_doi())`
  - `exporter/goldendict/export_help.py:336` — `make_citation(version, get_doi())`
  - `exporter/pdf/pdf_exporter.py:93` — `make_citation(self.version, get_doi())`
  - `tests/tools/test_version.py` — Zenodo lookup tests (lines ~160–275) and
    `get_doi` monkeypatches
  - `tests/tools/test_docs_update_how_to_cite.py:74` — `get_doi` monkeypatch
  - The Flutter app reads `db_info.citation` verbatim and needs no change.
- **Zenodo recorded the wrong author and type.** The record says creator `Bodhirasa`
  (the CFF's `name-suffix: Bhikkhu` was dropped) and resource type `Software` (the CFF's
  `type: dataset` was ignored). `uvx cffconvert -f zenodo` locally renders
  "Bodhirasa Bhikkhu", so Zenodo's own CFF reader behaves differently from the local
  tool and cannot be tested offline.
- **`.zenodo.json` overrides `CITATION.cff` on Zenodo.** Zenodo's docs
  (help.zenodo.org, "zenodo-json"): "If your repository contains both a `.zenodo.json`
  and a `CITATION.cff` file, Zenodo will only use the `.zenodo.json` metadata."
  `git check-ignore .zenodo.json` reports it is not ignored.
- **Monthly release flow today.** Local uposatha build → `tools/version.py` regenerates
  `CITATION.cff`, `tools/docs_update_how_to_cite.py` regenerates the docs page (both only
  on uposatha days) → user commits and pushes → `draft_release.yml` builds and creates a
  **draft** release → user publishes it → Zenodo archives it through its webhook.

## What it should do

1. **The concept DOI becomes a fixed constant** in `tools/version.py`
   (`DOI = "10.5281/zenodo.22979413"`), next to `WEBSITE`. Every caller that used
   `get_doi()` uses `DOI` instead. Every build, local or CI, then puts the DOI into
   `db_info.citation`, `db_info.doi`, `CITATION.cff`, the docs page, the GoldenDict
   `cite` entry, the PDF and (through `db_info`) the app.
2. **The Zenodo lookup machinery is deleted**: `get_doi`, `ensure_doi`,
   `fetch_zenodo_doi`, `_hit_is_dpd`, `ZENODO_API`, `ZENODO_REPO`, `DOI_PATTERN`, the
   now-unused imports (`json`, `os`, `re`, `urllib.*`, `config_read` if unused), and
   their tests. No network call remains in the build.
3. **A static `.zenodo.json` is added at the repo root** so that future Zenodo versions
   carry creator "Bodhirasa Bhikkhu", upload type `dataset`, the CC BY-NC-SA 4.0 licence,
   the title, the abstract and the keywords. It carries **no version or date**, so it
   never needs regenerating; Zenodo takes the version from the release.
4. **A test guards `.zenodo.json` against drift**: it parses the file and asserts the
   title, creator, description and keywords equal `AUTHOR`, `ABSTRACT` and `KEYWORDS` in
   `tools/version.py`.
5. **`kamma/tech.md` is corrected**: the DOI is now a constant, not a `config.ini` value
   looked up by `ensure_doi()`.

## What needs doing each month after this

Nothing new. The existing flow stays as it is. The one condition, already true in
September: the published release must point at a commit that holds that month's
regenerated `CITATION.cff`.

## Assumptions & uncertainties

- **Assumed:** Zenodo takes the version from the release tag when `.zenodo.json` has no
  `version` field. The Zenodo docs page does not say so. Checked after the October
  release (see "How we'll know it's done"). If wrong, the fix is to generate
  `.zenodo.json` from `tools/version.py` alongside the CFF.
- **Assumed:** when `.zenodo.json` has a `description`, Zenodo uses it instead of the
  release notes body. Same check.
- **Unverifiable before the next release:** that Zenodo reads `.zenodo.json` as
  intended. It can only be seen on the October record.
- **Known risk accepted:** if the repo is ever disconnected and reconnected on Zenodo, a
  new concept DOI is minted and the constant must be edited by hand. This is a one-line
  change and a rare event.
- **Not changed:** the September Zenodo record keeps "Bodhirasa / Software". The user
  can edit it by hand on zenodo.org (Edit → creators, resource type → Publish). Newer
  versions take their metadata from `.zenodo.json`.
- **Known side effect, not changed:** `mobile_release.yml` also creates non-prerelease
  drafts. When the user publishes one, Zenodo archives it as another version under the
  same concept DOI. Harmless for citation.

## Constraints

- Never edit `config.ini` (global rule). This design needs no `config.ini` change.
- Never run git commands. The user commits.
- `CITATION.cff` and `docs/how_to_cite.md` are generated and gated to uposatha days —
  do not hand-edit them. They pick up the DOI on the next uposatha build.
- Touch a file = own its lint: `ruff check --fix`, `ruff format`, `pyright` on every
  touched `.py` file; `just typecheck` before finishing. Do not run `ruff format` on
  `.zenodo.json`.
- Keep the existing function signatures (`make_citation(version, doi=None)` etc.) so
  the "no DOI → website" fallback tests stay meaningful.

## How we'll know it's done

- `rg -n "get_doi|ensure_doi|fetch_zenodo|zenodo.org/api|urllib" tools/ exporter/ tests/`
  returns nothing.
- `make_citation(version, DOI)` ends with `https://doi.org/10.5281/zenodo.22979413`.
- `uv run pytest tests/tools/ tests/exporter/goldendict tests/exporter/pdf` pass; the full
  suite passes; `just typecheck` 0 errors.
- `.zenodo.json` parses as JSON and the drift test passes.
- After the user's next uposatha build: `CITATION.cff` has
  `doi: 10.5281/zenodo.22979413`, `docs/how_to_cite.md` shows the DOI, and
  `sqlite3 dpd.db "select value from db_info where key='citation'"` ends with the
  doi.org link.
- After the October release is published: the new Zenodo version shows creator
  "Bodhirasa Bhikkhu", type Dataset, and the right version number.

## What's not included

- A DOI badge in `README.md` (not asked for).
- Editing the September Zenodo record (a manual step on zenodo.org, listed above).
- Stopping mobile-only releases from being archived.
- Per-entry DOIs (rejected in the citations thread).
