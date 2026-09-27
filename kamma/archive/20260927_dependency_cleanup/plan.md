# Plan: dependency cleanup

**Thread:** 20260927_dependency_cleanup
**Spec:** `spec.md` in this folder
**GitHub issue:** none

## Architecture Decisions
- Change dependencies only through `uv remove` / `uv add`, so `pyproject.toml` and `uv.lock`
  stay in step. Then run `uv sync --all-groups`. A bare `uv sync` strips the tools group.
- thefuzz, not raw rapidfuzz: it keeps fuzzywuzzy's lowercasing, so the gui2 suggestions
  do not change.
- The backup commit uses `subprocess` with `check=True`, so a failed commit raises
  `CalledProcessError` and prints its stderr through `pr.no`, as the gitpython error did.
- The MCP server goes to `archive/exporter/mcp/`, not into the existing `mcp_server/`.
  Two different versions should not mix.
- Small updates use `--upgrade-package` one package at a time. Open lower bounds make a
  blanket `--upgrade` jump the major versions.
- Output checks are function-level only (user decision). They live in a throwaway script
  in this thread's `artifacts/`, not in `tests/`, because the user deletes frozen
  golden-master tests. The one permanent new test is for the backup commit, which has no
  test today and talks to git.
- Deptry findings left after configuration are recorded here, not fixed.

## Phase 1 — Baseline, package swaps and removals

- [x] 1.1 Baseline: run `uv run pytest tests` and `just typecheck`. Record pass/fail counts here.
  → verify: counts pasted under this task. Pre-existing failures are named.
  - Result (2026-09-27): pytest `1913 passed, 12 deselected`. pyrefly `0 errors (95 suppressed)`.
    No pre-existing failures.
- [x] 1.2 Write `artifacts/capture_outputs.py` as described in spec item 7 (one output file
  per function). Run it: `uv run kamma/threads/20260927_dependency_cleanup/artifacts/capture_outputs.py
  kamma/threads/20260927_dependency_cleanup/artifacts/before`. Run it a second time into
  `artifacts/before2` and `diff -r` the two.
  → verify: every function in spec item 7 has a non-empty output file, or a recorded reason
    for being skipped. The two runs are identical. If not, strip the value that changes and re-run.
  - Result: 13 non-empty files, none skipped. The first before2 run differed only in the
    `/status` traffic-light colours (they follow system load), so those are now stripped too.
    After that, `diff -r before before2` is empty.
  - Notes: the `.ifo` date line and the RSS `lastBuildDate` are stripped. The PDF check records
    page count, metadata, outline and page text, not raw bytes. `read_dv_catalogue` writes
    `temp/sutta_codes_dupes.txt` as a side effect (gitignored). All 20 mp3s are non-silent, so
    the numpy check only proves the decode + RMS path still returns "not silent".
- [x] 1.3 Write `tests/db/backup_tsv/test_backup_dpd_headwords_and_roots.py` (spec item 7,
  last bullet). Run it against the current gitpython code.
  → verify: `uv run pytest tests/db/backup_tsv/` passes. Then break `git_commit` on purpose
    (drop the `--` paths so it commits the whole index) and confirm the staged-file assertion
    fails. Restore at once, in the same command.
  - Drift: uses the real `ProjectPaths(base_dir=tmp_path, create_dirs=False)` instead of a
    stand-in; it is simpler and type-safe. Added a second test: a failed commit (untracked
    paths after `--`) is reported through `pr.no`, not raised, and commits nothing.
  - Result: 2 passed on gitpython. With `git add` + whole-index commit patched in, both
    tests failed (`other.txt` swept into the commit). File restored, `cmp` identical, 2 passed.
- [x] 1.4 `uv remove --group tools prompt-toolkit google-auth-httplib2`
  → verify: `uv tree --all-groups --invert --package google-auth-httplib2` still shows
    google-api-python-client. `rg -n "prompt_toolkit" -g '*.py' -g '!**/archive/**'` shows nothing.
  - Result: both checks pass. prompt-toolkit is no longer in the lock at all.
  - Gotcha: `uv remove` syncs with the default groups only, so it uninstalled the whole tools
    group. `uv sync --all-groups` restored it. Later `uv add`/`uv remove` calls use `--no-sync`,
    followed by `uv sync --all-groups`.
- [x] 1.5 thefuzz swap: `uv remove --group tools fuzzywuzzy` and `uv add --group tools thefuzz`.
  Change the import in `tools/fuzzy_tools.py`.
  → verify: `uv run pytest tests/tools/test_fuzzy_tools.py` shows 5 passed. Ruff, format and
    pyright are clean on `tools/fuzzy_tools.py`.
  - Result: 5 passed. Ruff, format, pyright clean. `thefuzz>=0.22.1` added.
  - **OUTPUT DIFFERENCE — needs user decision.** The spec assumption "same results" is wrong.
    Of 30 capture terms, the top suggestion is the same in all 30, but the 2nd/3rd suggestion
    differs in 6 (e.g. `bs` → old `abs, cs, masc`, new `abs, sandhi, suffix`; `prr` → old
    `pr, prp, imperf`, new `pr, prefix, prp`).
  - Cause (measured, both libs side by side): `fuzz.ratio` is identical. `fuzz.partial_ratio`
    differs: fuzzywuzzy+python-Levenshtein gives `bs`/`sandhi` 0, `prr`/`prefix` 67; thefuzz
    (rapidfuzz) gives 67 and 80. rapidfuzz finds the best substring alignment; the old matching-
    block shortcut missed it. `WRatio` uses partial_ratio, so lower-ranked suggestions move.
- [x] 1.6 gitpython swap in `db/backup_tsv/backup_dpd_headwords_and_roots.py`: `import subprocess`,
  replace `Repo(...)` and `repo.git.commit(...)` with `subprocess.run([...], check=True,
  capture_output=True, text=True)`, and catch `CalledProcessError` (print stderr) and
  `FileNotFoundError`. Keep the `--` comment. Then `uv remove --group tools gitpython`.
  → verify: `uv run pytest tests/db/backup_tsv/` passes. Ruff, format and pyright are clean on
    both files. `uv tree --all-groups --invert --package gitdb` shows no remaining parent, or
    name any that remain. Do NOT run the backup script itself (it commits).
  - Result: 2 passed on the subprocess code. The failure test now prints git's own stderr
    (`error: pathspec ...`). Ruff, format, pyright clean on both files. gitpython, gitdb and
    smmap uninstalled; gitdb has no remaining parent. No `import git` left outside archive.
- [x] 1.7 Phase check: `uv sync --all-groups`, then `uv run pytest tests`. Run the capture
  script into `artifacts/after` and `diff -r artifacts/before artifacts/after`.
  → verify: test counts match 1.1, plus the new backup test. The diff is empty. Explain any
    difference here.
  - Result: `1915 passed, 12 deselected` (1913 + 2 new backup tests). `diff -r before after`
    differs only in `fuzzy_tools.txt` — the thefuzz scoring change recorded under 1.5.
    Every other output is identical. User accepted thefuzz's new ranking (2026-09-27).

## Phase 2 — Archive the MCP server

- [x] 2.1 In `tests/exporter/analysis/test_analysis_analyzer.py`, replace the three
  `from exporter.mcp.config import mcp_config` / `mcp_config.db_path` uses with
  `ProjectPaths().dpd_db_path` (`from tools.paths import ProjectPaths`).
  → verify: `uv run pytest tests/exporter/analysis/test_analysis_analyzer.py` gives the same
    result as the baseline. Ruff and format are clean.
  - Result: 24 passed (no failures at baseline). Ruff, format, pyright clean.
- [x] 2.2 Move `exporter/mcp/{server.py,config.py,README.md}` to `archive/exporter/mcp/`.
  Do not move the ignored `output/` or `__pycache__/`. Remove `exporter/mcp/output/*` from `.gitignore`.
  Then `uv remove --group tools mcp`.
  → verify: `rg -n "exporter.mcp|exporter/mcp" --hidden -g '!**/archive/**' -g '!kamma/**' -g '!conductor/**'`
    shows only the historical lines 8, 168 and 367 of `exporter/analysis/README.md`.
  - Result: files moved with plain `mv` (no git). `uv remove mcp` also dropped attrs, httpx-sse,
    jsonschema(+specifications), pydantic-settings, python-multipart, referencing, rpds-py and
    sse-starlette. `rg` finds no import of any of them and no FastAPI `Form`/`UploadFile` use.
  - **DEVIATION — `.gitignore` line kept for now.** `exporter/mcp/` still holds six ignored
    output files (2025-12-25 … 2026-01-14 analysis `.md`), an untracked 1-byte `__init__.py` and
    `__pycache__/`. Removing the ignore line would make the six files show up as untracked.
    Ask the user whether to delete the leftover folder; then drop the line.
  - Resolved: user said delete. `exporter/mcp/` removed and the `.gitignore` line dropped.
  - Sweep otherwise shows only README lines 8, 168, 367 (historical) plus that `.gitignore` line.
- [x] 2.3 Docs: remove the `mcp` entries from `docs/technical/project_folder_structure.md`
  (lines 28 and 129). Rewrite lines 154 and 364 of `exporter/analysis/README.md` to say the
  MCP server was archived to `archive/exporter/mcp/` on 2026-09-27.
  → verify: re-read both files. No text describes the server as live.
  - Result: done. NOTICED — NOT TOUCHING: `conductor/product.md` (lines 21, 24) and
    `conductor/tech-stack.md` (line 19) still describe the MCP server as a live feature. Left for
    the finalize doc sync.
- [x] 2.4 Phase check: `uv sync --all-groups`, then `uv run pytest tests` and `just typecheck`.
  → verify: same as after 1.7. No new errors.
  - Result: `1915 passed, 12 deselected`. pyrefly `0 errors (95 suppressed)`.

## Phase 3 — Small version updates

- [x] 3.1 Change the Flet pin to `flet[all]==1.0.1` in `pyproject.toml`. Then run
  `uv lock --upgrade-package` for each of: fastapi, uvicorn, prometheus-fastapi-instrumentator,
  httpx2, pre-commit, pyrefly, pyright, pytest, google-api-python-client, google-auth-oauthlib,
  google-genai, markdown, markdownify, mkdocs-material, numpy, pandas, pygithub, pyglossary,
  pypdf, python-levenshtein, flet. Then `uv sync --all-groups`. Check the output for `error:`.
  → verify: `uv tree --depth 1 --all-groups` shows sqlalchemy 2.0.x, filelock 3.x, ruff 0.15.x
    and anki 25.2.x. The listed packages are at their latest versions.
  - Result: sqlalchemy 2.0.50, filelock 3.29.1, ruff 0.15.16, anki 25.2.7 (held). `uv tree
    --outdated --depth 1` lists only those four. Updated: fastapi 0.136.3→0.141.1, uvicorn
    0.49.0→0.54.0, prometheus-fastapi-instrumentator 8.0.0→8.1.0, httpx2 2.4.0→2.13.1 (adds
    httpx2-jsfetch 1.0), pre-commit 4.6.2, pyrefly 1.1.1→1.3.1, pyright 1.1.414, pytest 9.1.1,
    google-api-python-client 2.200.0, google-auth-oauthlib 1.4.1, google-genai 2.8.0→2.25.0,
    markdown 3.11, markdownify 1.2.3, mkdocs-material 9.7.7, numpy 2.5.3, pandas 3.0.6,
    pygithub 2.10.0, pyglossary 5.4.2, pypdf 6.19.0, python-levenshtein 0.27.5, flet 1.0.1.
    No `error:` lines. Pre-phase lock copy kept in the session scratchpad.
- [x] 3.2 Phase check: `uv run pytest tests` and `just typecheck`. Re-run the capture script into
  `artifacts/after` and `diff -r artifacts/before artifacts/after`.
  → verify: tests match 1.7. The diff is empty. If a test failure or a diff traces to one
    upgrade, revert only that package's lock entry and record why here.
  - Result: `1915 passed, 12 deselected, 1 warning`. Capture diff: only `fuzzy_tools.txt` (1.5).
  - pyrefly 1.3.1 raised one new error: `exporter/analysis/ranking.py:118` `bad-argument-type`
    (it widens the `max(..., key=lambda, default=None)` lambda arg to include `None`). pyright is
    clean on the file, so per AGENTS.md this is a checker limitation: suppressed on that line
    with a reason. `just typecheck` → `0 errors (103 suppressed)`.
  - Suppressed 95 → 103, all from the pyrefly version (1.1.1 on today's tree still gives 95).
    Traced with `--enabled-ignores=pyre` on both versions: +2 are ignore comments — the new
    `ranking.py` one, and an existing `# type: ignore[return-value]` at
    `db/suttas/dv_catalogue_suttas.py:133` that now also hides a new `bad-return` (pandas
    `Hashable` keys). The other +6 are error kinds the `tests/**` sub-config turns off
    (tests-only run: 54 → 59; the sixth is not traced further). 0 errors either way.
  - NOTICED — NOT TOUCHING: pytest 9.1 warns `PytestRemovedIn10Warning` (class-scoped fixture
    defined as an instance method) in
    `tests/exporter/apple_dictionary/test_apple_dictionary_export.py::TestGenerateDictionaryXml`.
    It becomes an error in pytest 10. Follow-up.

## Phase 4 — Configure deptry

- [x] 4.1 Check the installed deptry's config keys (`uv run deptry --help`, deptry docs via
  Context7). Add `[tool.deptry]` to `pyproject.toml`: `extend_exclude` (resources, archive,
  tools/writemdict, temp, scripts/suttas), `non_dev_dependency_groups = ["tools"]`, and
  `per_rule_ignores` DEP002 for openpyxl, httpx2, pyicu, typst, ruff, pyright, pyrefly,
  pytest, pre-commit, deptry, mkdocs and mkdocs-material, each with a reason comment.
  → verify: `uv run deptry .` finishes. The report has no path under an excluded folder.
  - Result: deptry 0.25.1 accepts `extend_exclude`, `non_dev_dependency_groups` and
    `per_rule_ignores` (checked with `--help`). Config added before `[tool.pytest.ini_options]`,
    with `per_rule_ignores` as its own subtable so each entry carries a reason comment.
  - Drift: `"archive"` only matched the top-level folder (deptry uses `re.match`), so
    `audio/archive`, `conductor/archive` and `kamma/archive` still reported 14 findings. Changed
    to `"(.*/)?archive/"`. Report went 23 → 9 findings; none under an excluded folder.
  - Note: `uv run` rebuilds the local `dpd-db` package once after any `pyproject.toml` edit.
- [x] 4.2 Add a `deps` recipe to the `justfile` with a one-line comment, in the style of its
  neighbours: `uv run deptry .`
  → verify: `just --list` shows `deps`. `just deps` gives the same output as 4.1.
  - Result: added after `typecheck`. `just --list` shows it; `just deps` → `Found 9 dependency issues.`
- [x] 4.3 Record every remaining deptry finding here, with a one-line note on each. Fix only
  one-line, clearly correct items. Everything else is follow-up.
  → verify: the findings list is pasted under this task.
  - Findings (9) at first. Review showed 8/9 did have a one-line fix, so after review a
    `package_module_name_map` entry for python-levenshtein went in; `just deps` now reports 7.
    The recipe comment says it exits 1 while any finding remains.
    1. `conductor/tests/test_check_readmes.py:10` DEP001 `check_readmes` — sibling-module import in
       the retired conductor framework's tests. Follow-up: archive `conductor/tests/` or exclude it.
    2. `conductor/tests/test_generate_draft.py:4` DEP003 `conductor` — same cause.
    3. `conductor/tests/test_list_dirs.py:10` DEP001 `list_dirs` — same cause.
    4. `db/variants/extract_variants_from_cst.py:5` DEP004 `icecream` (dev) — debug `ic()` calls
       left in a build script. Follow-up: remove the `ic` calls or move icecream to `tools`.
    5. `db/variants/extract_variants_from_sya.py:7` DEP004 `icecream` — same.
    6. `gui2/utilities/sandhi_contraction_find_replace_gui.py:12` DEP004 `icecream` — same.
    7. `exporter/webapp/main.py:392` DEP003 `starlette` (`starlette.routing.Match`) — comes in
       through fastapi. Follow-up: declare starlette directly, or ignore it as fastapi's own layer.
    8. `pyproject.toml` DEP002 `python-levenshtein` and
    9. `scripts/find/most_common_missing_word_1_finder.py:11` DEP003 `Levenshtein` — one cause:
       `python-levenshtein` is a shim whose dependency `levenshtein` provides the `Levenshtein`
       module. Follow-up: depend on `levenshtein` directly (the user chose to keep the package,
       so this is their call), or add a `package_module_name_map` entry.

## Phase 5 — Final checks and star list

- [x] 5.1 Full gate: `uv run pytest tests`, `just typecheck`, and ruff check/format plus pyright
  on every touched `.py` file, including the capture script.
  → verify: all green except the baseline failures from 1.1.
  - Result: ruff check, ruff format --check and pyright clean on all 6 touched `.py` files;
    `pre-commit run --files` (those + pyproject.toml + justfile) passed. `1915 passed, 12
    deselected, 1 warning` (warning noted under 3.2). pyrefly `0 errors (103 suppressed)`.
- [x] 5.2 Sweep: `rg -n "^\s*(from|import) (fuzzywuzzy|git|mcp|prompt_toolkit)\b" -g '*.py' -g '!**/archive/**'`
  → verify: no hits.
  - Result: no hits.
- [x] 5.3 Delete `artifacts/before`, `artifacts/before2` and `artifacts/after`. Keep `capture_outputs.py`.
  → verify: `ls artifacts/` shows only the script.
  - Result: after the user accepted thefuzz, the three output folders and a `__pycache__/` were
    deleted. Only `capture_outputs.py` remains.
- [x] 5.4 Give the user the star/unstar list.
  Star: https://github.com/seatgeek/thefuzz
  Unstar: https://github.com/prompt-toolkit/python-prompt-toolkit,
  https://github.com/seatgeek/fuzzywuzzy, https://github.com/gitpython-developers/GitPython,
  https://github.com/modelcontextprotocol/python-sdk
  Keep: https://github.com/googleapis/google-cloud-python (google-auth-oauthlib still uses it).
  → verify: the list appears in the final message to the user.

## Post-review fixes (2026-09-27)

Reviews: Sonnet subagent, CodeRabbit, and a user-supplied independent review. See `review.md`.

- [x] R1 Archived MCP README: added an "archived" note saying its commands use the old path.
- [x] R2 `docs/technical/project_folder_structure.md`: added `archive/` to the tree and details.
- [x] R3 `tools/fuzzy_tools.py`: `List` → `list`, `typing` import dropped.
- [x] R4 Backup test: the failure test now asserts git's `pathspec` error is printed. Mutation
  check: with `pr.no("error")` patched in, 1 failed; restored (`cmp` identical), 2 passed.
- [x] R5 deptry: `package_module_name_map` for python-levenshtein (9 → 7 findings); recipe
  comment notes it exits 1 while findings remain.
- [x] R6 Plan 3.2: the 95 → 103 suppression change is accounted for.
- [x] R7 Flet 1.0.1: the package diff shows runtime changes (control diffing in
  `object_patch.py`, `page.py`, `messaging/session.py`, `raw_image.py`). Needs one gui2 launch
  and a normal edit by the user before finalize.
  → verify: user confirms gui2 opens and works.
  - Result: user confirmed `just gui` works on Flet 1.0.1 (2026-09-27).
- Gate after fixes: ruff/format/pyright clean on 6 files; `1915 passed, 12 deselected, 1 warning`;
  pyrefly `0 errors (103 suppressed)`.
