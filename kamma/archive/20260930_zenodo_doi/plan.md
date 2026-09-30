# Plan: Zenodo DOI in every citation, automatically

Spec: `kamma/archive/20260930_zenodo_doi/spec.md`. Background: `kamma/archive/20260906_citations/`.

## Architecture Decisions

- **The concept DOI is a constant, not a lookup.** It never changes, so looking it up
  every build adds a network call and a failure mode for nothing. The lookup also could
  not work: Zenodo's search does not find the record, and CI skipped it, so the shipped
  files would never carry the DOI. A constant in `tools/version.py`, next to `WEBSITE`,
  reaches local and CI builds alike.
- **Callers pass `DOI` explicitly; signatures stay `doi: str | None = None`.** This is
  the smallest change to the three call sites and keeps the existing "no DOI → website"
  tests valid.
- **`.zenodo.json` is static, not generated.** It holds no version or date, so it has
  nothing to go stale monthly. Drift in the abstract/keywords/author is caught by a test
  rather than by a generator. Generating it is the fallback if Zenodo does not take the
  version from the tag.
- **Delete, don't disable, the lookup code** (`get_doi`, `ensure_doi`,
  `fetch_zenodo_doi`, `_hit_is_dpd`, their constants and tests). Dead network code is
  the kind that later gets "fixed" back to life.

## Baseline

- [x] Record the baseline before any edit.
  → verify: `uv run pytest tests/` and `just typecheck`; paste pass/fail counts here.
    **Result:** 1916 passed, 12 deselected; typecheck 0 errors (103 suppressed). Clean.
    `resources/tpr_downloads` was already modified before this thread — not touched.

## Phase 1 — DOI constant everywhere, lookup removed

- [x] `tools/version.py`: add `DOI = "10.5281/zenodo.22979413"` beside `WEBSITE` with a
      one-line WHY comment (concept DOI, always resolves to the newest release, changes
      only if the repo is reconnected on Zenodo). Delete `ZENODO_API`, `ZENODO_REPO`,
      `DOI_PATTERN`, `get_doi`, `_hit_is_dpd`, `fetch_zenodo_doi`, `ensure_doi` and the
      old comment block above them. In `main()`, replace `doi = ensure_doi()` with
      `DOI` passed to `update_db_version` and `update_citation_cff`. Remove imports that
      become unused (`json`, `os`, `re`, `urllib.*`, `config_read`).
  → verify: `uv run ruff check --fix tools/version.py`, `uv run ruff format tools/version.py`,
    `uv run pyright tools/version.py` → 0 errors.
    **Result:** clean; diff is +7 / −82.
- [x] Replace `get_doi()` with `DOI` in `tools/docs_update_how_to_cite.py`,
      `exporter/goldendict/export_help.py` and `exporter/pdf/pdf_exporter.py` (imports
      and call sites).
  → verify: `rg -n "get_doi|ensure_doi|fetch_zenodo" --glob '!kamma/**' --glob '!archive/**' --glob '!graphify-out/**' .`
    returns only test hits (fixed next task); ruff check, ruff format, pyright clean on
    all three files.
    **Result:** only test hits remained; all three files clean.
- [x] Tests: in `tests/tools/test_version.py` delete the Zenodo lookup tests
      (`FakeResponse`, `_hits`, `_record`, `test_zenodo_query_is_a_quoted_phrase`,
      `test_rejects_*`, `test_accepts_the_dpd_record`,
      `test_a_network_error_is_reported_not_swallowed`, `test_ensure_doi_*`). Add one
      test: `make_citation(VERSION, version.DOI)` ends with
      `https://doi.org/10.5281/zenodo.22979413`. In
      `tests/tools/test_docs_update_how_to_cite.py` drop the `get_doi` monkeypatch and
      assert the regenerated page contains `10.5281/zenodo.22979413`.
  → verify: `uv run pytest tests/tools/test_version.py tests/tools/test_docs_update_how_to_cite.py`
    all pass; ruff and pyright clean on both files. Revert-check: in one command,
    change `make_how_to_cite_md(version, DOI)` to `make_how_to_cite_md(version, None)`,
    run the docs-page test, confirm it fails, and restore the line.
    **Result:** 22 passed. Revert-check: `test_page_is_rewritten_on_an_uposatha` failed
    with `None`, passed again after restore. Ruff removed the now-unused `json` import.
- [x] Render check of the offline and PDF citations.
  → verify: `uv run python -c` snippet calling `make_citation(config version, DOI)` via
    the same import path as `export_help.add_citation` and `pdf_exporter.GlobalVars`
    prints the doi.org link; `uv run pytest tests/exporter/goldendict tests/exporter/pdf`
    pass.
    **DRIFT:** there is no `tests/exporter/pdf`; ran `uv run pytest tests/exporter`
    instead → 542 passed. Both import paths print
    `… Version v0.4.20260930. https://doi.org/10.5281/zenodo.22979413`.

## Phase 2 — Zenodo record metadata

- [x] Add `.zenodo.json` at the repo root:
      ```json
      {
        "title": "Digital Pāḷi Dictionary",
        "upload_type": "dataset",
        "creators": [{"name": "Bodhirasa Bhikkhu"}],
        "description": "<ABSTRACT from tools/version.py, verbatim>",
        "license": "cc-by-nc-sa-4.0",
        "keywords": ["Pāḷi", "Pali", "dictionary", "lexicography", "Buddhism", "Theravāda"],
        "access_right": "open"
      }
      ```
      No `version`, no `publication_date`. Write it programmatically from the constants
      (UTF-8, `ensure_ascii=False`, indent 2) so the text matches byte for byte; do not
      run `ruff format` on it.
  → verify: `python3 -m json.tool .zenodo.json` succeeds; `git check-ignore .zenodo.json`
    exits 1 (not ignored).
    **Result:** JSON valid; not ignored.
- [x] Drift test in `tests/tools/test_version.py`: parse `.zenodo.json`; assert
      `title`, `creators[0].name == AUTHOR`, `description == ABSTRACT`,
      `keywords == KEYWORDS`, `license == "cc-by-nc-sa-4.0"`, and that `version` is
      absent.
  → verify: test passes; edit one keyword in a scratch copy of the constants and confirm
    it fails, restore in the same command.
    **Result:** passes; with `"lexicography"` changed to `"lexicon"` it failed, and it
    passed again after restore. `json` import re-added for this test.

## Phase 3 — Docs and final checks

- [x] `kamma/tech.md`: rewrite the citation bullet — the concept DOI is the `DOI`
      constant in `tools/version.py`; `.zenodo.json` controls the Zenodo record and
      overrides `CITATION.cff` there; no lookup, no `config.ini` key.
  → verify: `rg -n "ensure_doi|\[version\] doi" kamma/tech.md` returns nothing.
    **Result:** nothing.
- [x] Full checks.
  → verify: `uv run pytest tests/` passes (count vs baseline, minus deleted tests, plus
    new ones); `just typecheck` 0 errors; `uv run pyright` on every touched `.py` file
    0 errors; `uv run graphify update .`.
    **Result:** 1911 passed (1916 − 7 deleted lookup tests + 2 new); typecheck 0 errors;
    pyright 0 errors on all 6 touched `.py` files.
- [x] Hand the user the post-merge checks (report only, no action by the agent):
      1. Next uposatha build: `CITATION.cff` has the `doi:` line, the docs page shows
         the DOI, `db_info.citation` ends with the doi.org link.
      2. After publishing the October release: the new Zenodo version shows
         "Bodhirasa Bhikkhu", type Dataset, correct version. If the version is missing,
         switch `.zenodo.json` to generated (see spec assumptions).
      3. Optional: fix the September record by hand on zenodo.org.
  → verify: the three checks appear in the final summary.

## Review fixes (2026-09-30)

- [x] Behaviour tests for the three unguarded call sites: `version.main()` (db_info
      `citation`/`doi` + CFF), GoldenDict `add_citation`, PDF `GlobalVars.citation`
      (new `tests/exporter/pdf/test_pdf_exporter.py`).
  → verify: each fails with `DOI` replaced by `None` at its call site, passes restored.
    **Result:** 1 failed each when broken; full suite 1914 passed; typecheck 0 errors.
- [x] `DOI` import reordered in `tools/docs_update_how_to_cite.py`.
  → verify: ruff/pyright clean.
