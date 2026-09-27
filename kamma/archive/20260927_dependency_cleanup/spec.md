# Spec: dependency cleanup

**Thread:** 20260927_dependency_cleanup
**GitHub issue:** none

## Overview
A review of the project's Python dependencies (2026-09-27) found unused packages, one
unmaintained package, one heavy package used for a single git call, one retired
feature, and a dependency checker (deptry) that is installed but not configured.
The user made eight decisions one at a time. This thread carries out the five that
change something. It also ends with a list of GitHub repos to star and unstar.

## What it should do

1. **Remove unused packages** from `[dependency-groups].tools` in `pyproject.toml`:
   - `prompt-toolkit`: no imports anywhere. Its only user, `scripts/fix/fix_synonym_entries.py`,
     was deleted in commit acd85c53.
   - `google-auth-httplib2`: no imports. `google-api-python-client` already depends on it,
     so it stays installed.

2. **Replace fuzzywuzzy with thefuzz.** thefuzz is fuzzywuzzy under its new name, with the
   same API. Version 0.22.1 depends only on `rapidfuzz>=3,<4`.
   - `tools/fuzzy_tools.py`: change `from fuzzywuzzy import process as fuzzy_process`
     to `from thefuzz import process as fuzzy_process`. `extractBests` stays.
   - Callers (no change needed): `gui2/dpd_fields.py` (3 calls), `gui2/dpd_fields_family_set.py`.
   - `exporter/webapp/toolkit.py` has its own unrelated `find_closest_matches`. Do not touch it.
   - `pyproject.toml`: swap `fuzzywuzzy>=0.18.0` for `thefuzz`.
   - **Keep `python-levenshtein`** (user decision). `scripts/find/most_common_missing_word_1_finder.py`
     still uses `Levenshtein.distance`.

3. **Drop gitpython from the TSV backup.** `db/backup_tsv/backup_dpd_headwords_and_roots.py`
   uses `from git import Repo` only in `git_commit()`, which runs
   `repo.git.commit("-m", "pali update", "--", *files_to_add)`.
   - Replace it with `subprocess.run(["git", "commit", "-m", "pali update", "--", *files_to_add],
     check=True, capture_output=True, text=True)`.
   - Keep the path-limited `--` commit and its existing comment. That comment explains why
     the commit must not sweep up other sessions' staged files.
   - Keep the behaviour on failure: print the error through `pr.no(...)`. Catch
     `subprocess.CalledProcessError` and show its stderr. Also catch `FileNotFoundError`
     for a missing git binary. Do not use a bare `except Exception`.
   - Remove `gitpython` from `pyproject.toml`. That uninstalls gitpython, gitdb and smmap,
     unless another package needs them (check `uv tree --invert`).

4. **Archive the MCP server** (the user no longer uses it).
   - Move `exporter/mcp/` (`server.py`, `config.py`, `README.md`) to `archive/exporter/mcp/`.
     `archive/exporter/mcp_server/` already exists from an older version, so use a separate
     folder name. The ignored `output/` and `__pycache__/` folders do not move.
   - `tests/exporter/analysis/test_analysis_analyzer.py` imports `mcp_config` three times
     (lines ~155, ~196, ~218), only to get the db path. Replace this with
     `ProjectPaths().dpd_db_path`. That is exactly what `MCPConfig` read.
   - Update the docs that still describe the server as live:
     `docs/technical/project_folder_structure.md` (lines 28 and 129) and
     `exporter/analysis/README.md` (lines 154 and 364). Leave the historical notes
     (lines 8, 168 and 367) as they are.
   - Remove the `.gitignore` line `exporter/mcp/output/*`.
   - Remove `mcp` from `pyproject.toml`.

5. **Apply small version updates only.** A plain `uv lock --upgrade` would jump SQLAlchemy
   to 2.1, filelock to 4 and Ruff to 0.16, because their lower bounds are open. Use
   `uv lock --upgrade-package <name>` for each package below:
   fastapi, uvicorn, prometheus-fastapi-instrumentator, httpx2, pre-commit, pyrefly,
   pyright, pytest, google-api-python-client, google-auth-oauthlib, google-genai,
   markdown, markdownify, mkdocs-material, numpy, pandas, pygithub, pyglossary, pypdf,
   python-levenshtein.
   - Flet is pinned to `==1.0.0`. Change the pin to `==1.0.1`.
   - Do not upgrade: sqlalchemy, filelock, ruff, anki (anki is pinned `<25.3` for protobuf).

6. **Configure deptry** so it gives a useful report. Today it reports 587 issues, and
   almost all are false.
   - Add `[tool.deptry]` to `pyproject.toml`: `extend_exclude` for `resources`, `archive`,
     `tools/writemdict`, `temp` and `scripts/suttas`, and `non_dev_dependency_groups = ["tools"]`.
     The second setting makes deptry check the tools group for unused packages. By default
     it treats that group as dev, and it never checks dev packages for use.
   - Add known-good exceptions with a reason, in the same style as the repo's inline comments:
     `openpyxl` (pandas engine), `httpx2` (TestClient backend), `pyicu` (pyglossary slob),
     `typst` (CLI), and the CLI-only tools `ruff`, `pyright`, `pyrefly`, `pytest`,
     `pre-commit`, `deptry`, `mkdocs`, `mkdocs-material`.
   - Add a `just deps` recipe that runs `uv run deptry .`.
   - Whatever deptry still reports goes into `plan.md` as findings. Do not fix any of it
     in this thread unless it is one line and clearly correct.

7. **Check function output before and after.** The test suite does not show whether a
   package swap or upgrade changes real output. Check at function level only, never by
   running whole exports or builds (user decision).
   - Write one throwaway script:
     `kamma/threads/20260927_dependency_cleanup/artifacts/capture_outputs.py <out_dir>`.
     It calls each function below on fixed real input and writes one text file per
     function into `<out_dir>`. Run it before any change (`artifacts/before/`) and again
     after Phase 1 and after Phase 3 (`artifacts/after/`), then `diff -r`.
   - This is a one-off harness, not a committed snapshot test. The user deletes frozen
     golden-master tests, so none go into `tests/`. The output folders are deleted at
     finalize. The script is kept with the thread.
   - Functions and inputs (each one is guarded by the package in brackets):
     - `tools/fuzzy_tools.find_closest_matches` [fuzzywuzzy → thefuzz]: about 30 misspelt
       terms against the real `family_set` names and the real `pos` values from `dpd.db`.
     - `tools/rss_feed.parse_newsletters` + `render_rss` [markdown] on `docs/newsletters.md`.
     - `markdownify` + `scripts/build/newsletter_scraper.strip_footer` [markdownify] on the
       HTML bodies that `parse_newsletters` returns.
     - `tools/goldendict_exporter.create_glossary` + `add_data` + `write_to_file`
       [pyglossary] with 3 fixed entries, written to a temp folder. Record the written files.
     - `exporter/pdf/pdf_exporter.merge_chunks` [pypdf] on two tiny PDFs made with the
       `typst` package, with a minimal `GlobalVars` stand-in. If the stand-in needs more
       than about 20 lines, drop this item and record why in `plan.md`.
     - `db/suttas/dv_catalogue_suttas.read_dv_catalogue` [pandas] on the local
       `db/suttas/dv_catalogue_suttas.tsv`.
     - `audio/error_check/delete_silent_files.check_file` [numpy, miniaudio] on the first
       20 mp3s it finds. Skip if the audio folder is not on disk.
     - Webapp responses [fastapi, uvicorn, starlette] through `TestClient`, as the tests in
       `tests/exporter/webapp/` do: `/`, a word search, a permalink, `/status`. Strip
       values that change on every run (times, memory figures) before writing.
   - Expected result: no differences. Record any difference in `plan.md` with its cause.
     Never accept a difference silently.
   - **The TSV backup commit gets a real, permanent test** in
     `tests/db/backup_tsv/test_backup_dpd_headwords_and_roots.py`. It calls `git_commit`
     in a temp git repo (`tmp_path`, `git init`, `monkeypatch.chdir`) with a small
     stand-in for `ProjectPaths` whose `pali_word_path` points into that repo. It asserts
     that only the part TSVs are committed with the message "pali update", and that a file
     staged beforehand stays staged and uncommitted. Write it and see it pass on gitpython
     before the swap, then again after it.

8. **End with a star/unstar list** for the user:
   - Star: thefuzz, https://github.com/seatgeek/thefuzz
   - Unstar: prompt-toolkit, fuzzywuzzy, GitPython, MCP Python SDK
     (links in plan task 5.4).
   - Keep the star on google-cloud-python. google-auth-oauthlib is still used and lives there.

## Assumptions & uncertainties
- Verified: import counts (rg across all `.py` files, archive excluded), `uv tree --invert`
  results, thefuzz 0.22.1 metadata on PyPI, the repo seatgeek/thefuzz (not archived),
  the MCP config users, and that the docs builder installs pathspec.
- Assumption: thefuzz's `extractBests` gives the same results as fuzzywuzzy with
  python-Levenshtein. The five tests in `tests/tools/test_fuzzy_tools.py` must stay green.
  **Disproved 2026-09-27:** the top suggestion matches, but 2nd/3rd suggestions change in
  6 of 30 capture terms, because rapidfuzz's `partial_ratio` scores differently. The user
  accepted the new order; details in `plan.md` task 1.5.
- The leftover ignored files in `exporter/mcp/` (old outputs, `__init__.py`, `__pycache__/`)
  were deleted at the user's request, then the `.gitignore` line was removed.
- Assumption: the deptry exception keys (`non_dev_dependency_groups`, `per_rule_ignores`)
  match the installed deptry version. Check against `deptry --help` first.
- Unknown: whether FastAPI 0.136→0.141 or uvicorn 0.49→0.54 change behaviour. The webapp
  tests are the guard.
- The backup script makes a real git commit, so it is never run in this thread.

## Constraints
- Shared working tree: never stash, restore or reset. Stage nothing. The user commits.
- Every touched `.py` file passes `ruff check`, `ruff format` and `pyright`. `just typecheck` passes.
- Use `uv add` / `uv remove` for dependency changes, then `uv sync --all-groups`.

## How we'll know it's done
- `uv run pytest tests` passes. This includes the fuzzy tools and passage-analyser tests.
- `just typecheck` passes.
- `just deps` gives a short report. No finding comes from the submodules or archive.
- `rg` finds no import of fuzzywuzzy, git (gitpython), mcp or prompt_toolkit outside `archive/`.
- `uv tree` shows sqlalchemy 2.0.x, filelock 3.x, ruff 0.15.x and anki 25.2.x.
- `diff -r artifacts/before artifacts/after` shows no differences, or each difference is
  explained in `plan.md`.
- The new backup commit test passes both before and after the gitpython swap.

## What's not included
- Major upgrades: SQLAlchemy 2.1, filelock 4, Ruff 0.16, anki.
- Replacing unidecode or python-levenshtein, and archiving the gitignore cleaner.
  The user decided to keep all three.
- The Go modules and the browser extension's npm packages.
- Output checks by whole process: full GoldenDict, PDF, docs or TPR builds. Functions only.
- Function checks for packages that are not changed here, and for the PTS concordance
  reader (it needs a download; no local xlsx exists).
