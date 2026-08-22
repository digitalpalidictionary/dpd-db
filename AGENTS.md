# Project Rules

Specific to dpd-db. Global rules are in `~/.claude/CLAUDE.md`.

## Project Overview

Everything related to the Digital Pāḷi Dictionary. Edit the db with `/gui2`, build with `/db`, test with `/db_tests`, export with `/export`.

Detailed specs live in `conductor/` — `product.md` (vision, features, audience, release schedule) and `tech-stack.md` (stack and key libraries). Read the relevant one before working in an unfamiliar area.

Four main parts: **db** (build and populate tables), **db_tests** (data integrity), **gui2** (add/edit words), **exporter** (compile and export formats). Folder layout: `docs/technical/project_folder_structure.md`.

## Kamma
- When a thread passes review, run the full `/kamma:4-finalize` sequence immediately — don't stop after archiving; also do the GitHub comment and reflect/lessons steps.
- Never pause a thread to ask for commit permission at phase checkpoints. The user commits everything at the end; checkpoint steps are report-only.

## Concurrent Threads (working tree safety)
Multiple kamma threads regularly run against this repo in the same working tree at once.
- Before staging, snapshot `git status --porcelain` and cross-reference every entry against "did this thread touch this file". Stage by explicit file list — never `git add <dir>` or `git add -A`.
- **NEVER run `git stash`, `git checkout -- <path>`, `git restore`, or `git reset --hard` here.** They operate on the whole tree and silently destroy other sessions' uncommitted work. This has happened: during the pyrefly thread (2026-07-27) another session's sweep wiped a completed phase three times — the third removed a `[tool.pyrefly]` config block, a justfile recipe, a dependency, twelve verified fixes, and resurrected three deliberately deleted files.
- Damage is worst mid-thread, because it reverts unevenly — some files come back, others don't, and the result looks like a working tree, not a broken one. If a tool reports a file "was modified, either by the user or by a linter" and the content is your pre-edit version, treat it as a rollback and **audit every file you have touched** before continuing.
- To test against a clean tree, use `git worktree add <path>`.
- To discard your own changes, revert the specific files by name, never a whole-tree command.

## Python Conventions
- Add type hints everywhere, especially where missing. Modern forms only: `dict[str, str]`, `tuple[str, str]`, `list[str]`, `X | None` — not `Dict`/`Tuple`/`List`/`Optional`.
- Use `Path` from pathlib for filepaths, not `os`.
- Debug with `icecream` (`from icecream import ic`; `ic(variable_name)`), not `print()`.
- NEVER use `sys.path` hacks or `Path(__file__).resolve().parents[n]`. Assume the script runs from the project root.
- `.gitignore` ignores ALL `__init__.py` files repo-wide, so a package `__init__.py` re-export can never be committed. Import new symbols from their concrete module (`from tools.cst_source.corpus_index import CstSourceIndex`).

## SQLAlchemy ORM Objects
- Never mutate ORM objects unless the explicit purpose is to update, change, or delete them in the database.
- Compute temporary or derived values separately (a dict or local) — never write them back to a tracked ORM attribute as a side-effect.

## Data
- For questions about actual dictionary data (which source codes exist, how a field is populated, row counts), query the live `dpd.db` directly. `db/backup_tsv/` files are regenerated backups, not the source of truth. Don't infer data shape from TSVs or downstream exporter code.
- `db_tests` failures on freshly imported draft entries are the editor's per-word checklist, not import defects. Pre-fix only what zero-exception evidence in the live db demands (closed vocabularies like `verb`, absolutes like "`source_1` never without `example_1`", `lemma_2` = nominative singular, `(gram)` rows always carry `family_set grammatical terms`). Leave per-word lexicographic judgement (`compound_type`, `construction`, `derived_from`, `neg`) to the human.
- Any git-tracked data file written by code (e.g. `tools/speech_marks.json`) must be saved in canonical sort order — `pali_sort_key` for Pāḷi strings, applied to both keys and value lists. Insertion order turns every regeneration into a full-file reorder diff.

## Database Model (`db/models.py`)

| Class | Table | Purpose |
|---|---|---|
| `DpdHeadword` | `dpd_headwords` | Main entries — ~60 columns + many `@cached_property` helpers |
| `DpdRoot` | `dpd_roots` | Pāḷi verbal roots |
| `Lookup` | `lookup` | Fast index — every inflected form → headword IDs |
| `SuttaInfo` | `sutta_info` | Sutta metadata (SC, CST, BJT links) |
| `InflectionTemplates` | `inflection_templates` | Stem/ending grids for inflection tables |
| `FamilyRoot` | `family_root` | Root family groupings with HTML |
| `FamilyWord` | `family_word` | Word family groupings |
| `FamilyCompound` | `family_compound` | Compound family groupings |
| `FamilyIdiom` | `family_idiom` | Idiom groupings |
| `FamilySet` | `family_set` | Thematic set groupings |
| `BoldDefinition` | `bold_definitions` | Bold-text definitions from commentaries |
| `DbInfo` | `db_info` | Key-value store for metadata and cached sets |

- `DpdHeadword` relationships: `.rt` → `DpdRoot`, `.fr` → `FamilyRoot`, `.fw` → `FamilyWord`, `.it` → `InflectionTemplates`, `.su` → `SuttaInfo`
- Key columns: `id`, `lemma_1` (unique), `pos`, `meaning_1`, `root_key`, `family_root`, `family_compound`, `stem`, `pattern`, `inflections`, `inflections_html`, `construction`
- JSON pack/unpack: many string columns store JSON — access via `foo_pack(list)` / `foo_unpack` (e.g. `headwords_pack` on `Lookup`).
- **Empty-string gotcha:** `DpdHeadword.inflections_list_all` yields `""` entries when either inflections column is empty — filter empty strings before using inflections as dict keys or set members.
- Full column docs: `docs/technical/dpd_headwords_table.md`.
- Weekly, or whenever the model changes, check `db/models.py` matches `docs/technical/dpd_headwords_table.md`. Same cadence for the tree vs `docs/technical/project_folder_structure.md`.

## Shared Tools

**`tools/db_helpers.py`** — `get_db_session(db_path)` returns a Session (exits with error if missing); `create_db_if_not_exists(db_path)`; `create_tables(db_path)`; `get_column_names(table_class)` → `list[str]`.
```python
from db.db_helpers import get_db_session
db = get_db_session(Path("dpd.db"))
```

**`tools/configger.py`** — reads/writes `config.ini`. `config_read(section, option)` → `str | None`; `config_update(section, option, value)`; `config_test(section, option, value)` → `bool`. Sections: `version`, `regenerate`, `deconstructor`, `gui`, `goldendict`, `dictionary`, `exporter`, `apis`, `anki`, `simsapa`, `tpr`.

**`tools/printer.py`** — coloured console output with timing (`from tools.printer import printer as pr`).
- Timers: `pr.tic()` / `pr.toc()` (main clock), `pr.bip()` / `pr.bop()` (mini clock, returns elapsed string), `pr.print_bop()`.
- Need an ending — follow with `pr.yes(msg)` or `pr.no(msg)` (right-aligned, max 8 chars): `pr.green_tmr()`, `pr.cyan_tmr()`, `pr.white_tmr()`.
- Standalone: `pr.yellow_title()`, `pr.green_title()`, `pr.green()`, `pr.cyan()`, `pr.white()`, `pr.red()`, `pr.amber()`, `pr.counter(counter, total, word)`, `pr.summary(key, value)`.

## Go
- `go_modules/` has many `package main` directories. Never `go build ./go_modules/<single-package-path>/` — with no `-o` and one main target, Go writes a multi-MB binary into the repo root. Use `go build ./go_modules/...` or `go vet`, or pass `-o <scratchpad-path>`.
- Invoke with `go run ./go_modules/<pkg>` (package form), never the glob form `go run go_modules/<pkg>/*.go` — the glob sucks in `*_test.go` and hard-fails with `cannot run *_test.go files` (this broke CI in #231).
- The frequency-table system is **purely positional**. `loadCorpus` in `go_modules/frequency/main.go` discards the `*_file_map.json` section keys and keeps only their order; `frequency/templates/frequency_template.html` hardcodes per-corpus slot indices (SYA slots 8/9/10 = Khuddaka 1/2/3). Adding, removing, or reordering a section shifts every later `{{index .XxxFreq N}}` and breaks the template plus every snapshot fixture. To re-bucket a text packed inside a combined source volume, do NOT change the section list — split the file at a stable heading in `frequency/setup/4SYA.go` into synthetic `<path>::slice` freq keys and point each slice at its correct existing section in `sya_file_map.json`. Verify by replaying `loadCorpus`/`freqFinder` in Python against the regenerated `shared_data/frequency/*_file_freq.json` rather than rebuilding `dpd.db`.

## Dependencies
- Manage with astral uv. Install with `uv add`, never `pip install` or `uv pip install`. Don't run scripts with uv unless asked.
- **Optional/transitive deps belong to their parent.** If a package is only needed because another loads it (an engine, backend, or feature plugin), declare it through the parent's extra — it self-documents and auto-removes if the parent is dropped. These are dynamic, string-keyed imports (`pd.read_excel` → `import_optional_dependency("openpyxl")`), so no static tool can see them and a bare entry looks unused and gets wrongly pruned.
- EXCEPTION — keep it bare WITH an inline comment naming the owner when the extra is unusable: too broad (bare `openpyxl` for `pd.read_excel`, since `pandas[excel]` pulls five engines), or no extra provides it (`httpx2` is starlette's TestClient backend; no fastapi/starlette extra ships it). The comment is mandatory so it never again looks orphaned.
- Before removing an apparently unused dep, confirm it isn't a parent's optional engine, then re-run the full test suite AND a build cycle. `uv sync` succeeding proves nothing about dynamic imports.

## Docs Lookups
- Flet: see `resources/flet-docs`.
- Context7 MCP for up-to-date docs on `SQLAlchemy`, `Flet`, `FastAPI`, `aksharamukha`, `requests`.

## Testing

- Mirror the source structure: `exporter/webapp/main.py` → `tests/exporter/webapp/test_main.py`.
- Run: `uv run pytest tests/` · a file: `uv run pytest tests/path/to/test_file.py` · timings: `--durations=10`.
- Slow tests (large CST XML parsing) are marked `@pytest.mark.slow` and deselected by default. Run with `uv run pytest -m slow`. Mark new big-source tests `slow`.

### Pre-commit gate
- **TOUCH A FILE = OWN ITS LINT.** Editing any file makes you responsible for `ruff check` AND `pyright` passing on it — including PRE-EXISTING errors you didn't introduce. The hook stages the whole file and rejects the commit on any error in it, so "it was already broken" is not an out. Fix every error with a real, behaviour-preserving fix (never `# noqa`). This is a repeated issue.
- After editing any file, run, in order: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright <file>`, `uv run pytest <related test paths>`. Do NOT skip `ruff format` — a file can pass `ruff check` and still be rewritten by the formatter, bouncing the commit.
- Exception: skip `ruff format` on `.json` fixtures — it adds trailing commas that break parsing. Regenerate fixtures programmatically.
- The top-level `exclude:` in `.pre-commit-config.yaml` only covers `archive/`, `scripts/archive/`, `scripts/bash/`, `tools/writemdict/`. `gui2/` is pyright-excluded but NOT ruff-excluded, so it commonly carries pre-existing ruff violations that surface when you touch a file.
- If a related test file was broken before your changes, note it — don't silently ignore, it may mask a regression.

### Repo-wide type check: `just typecheck`
- Runs **pyrefly** across the whole repo (config in `[tool.pyrefly]` in `pyproject.toml`). Run before finishing any thread. CI enforces it on every push to `main` and every PR via `.github/workflows/typecheck.yml`.
- **A different job from pyright, not a replacement.** pyright is the per-file commit gate; pyrefly is the whole-repo sweep, catching a change that breaks a caller in a file you didn't stage. It checks ~390 files in ~15 seconds. Deliberately NOT in `.pre-commit-config.yaml`.
- **When they disagree, pyright wins** (97.8% vs 87.8% spec conformance) — treat a pyrefly-only complaint as a checker limitation to suppress narrowly.
- **A pyrefly fix isn't done until `uv run pyright <file>` is also clean.** Satisfying one regularly breaks the other, and only pyright blocks the commit. This bit twice in one thread. Run both, every time.
- Suppress with `# pyrefly: ignore` **plus a reason on the same comment**, only for genuine limitations (unannotated upstream APIs, a `locals()` guard, `lru_cache` collapsing overloads). Never to duck a real bug.
- `[tool.pyrefly].project-excludes` goes beyond pyright's: `scripts/suttas/**` is one-off corpus extraction nothing imports.

## GitHub
Unless specified, the repo is https://github.com/digitalpalidictionary/dpd-db.

- **Commit only when asked, NEVER unasked.** Format, all lowercase: `#issue area: change1, change2` (e.g. `#67 webapp: updated css, fixed overflow`). Max 72 chars on the first line.
- This repo has an automated "data update" commit habit running independently of any session, which can re-track a file you `git rm --cached`'d earlier (it happened to `tools/proofreader.tsv`). Before finalizing a thread that untracked a file, verify with `git ls-files <path>`.
- **NEVER write to GitHub issues unless specifically asked.** This covers ALL writes: creating, commenting, editing body/title, checklist items, closing/reopening, labelling. Noticing a follow-up is not a licence to touch the tracker — report it to the user.
- Write issue comments in the user's style: short, direct, lowercase sentence starts, minimal punctuation.
- "Solve" means read the specified issue with get_issue and offer solutions — don't overthink, just read it. Ask the user to open the files you need. Judge whether it's a straightforward fix or needs solving at a higher level. Show code snippets of suggested changes.

## Performance Work
- Before implementing any optimization spec, re-derive its numbers from the actual profiling log (`logs/makedict_*.html`) and benchmark the claimed mechanism on a throwaway copy (`cp dpd.db /tmp/...`). Two of five premises in one thread were wrong, one destructively so.
- The recurring makedict bottleneck is ORM loops over large tables (load-all + per-row mutate + commit). Replace with a single `executemany` on the session's own connection — pattern: `tools/lookup_sync.py:_raw_sql_sync`. Never `INSERT OR REPLACE` on `lookup` (blanks the other 16 columns); use `ON CONFLICT ... DO UPDATE SET <col> = excluded.<col>`.
- `db_session.close()` is NOT a valid finding for short-lived build scripts. SQLAlchemy 2.0 has no `__del__`; the OS releases connections on process exit. Do not flag it.

## Export Flags
- The local justfile recipes `export-mobile` (dpd-db) and `build-db` (dpd-flutter-app) MUST pass the same `mobile_exporter.py` flags (`--cone --peu --wordnet`) so a local build equals the packaged DB. Keep both in sync.
- The CI release workflows (`mobile_release.yml`, `draft_release.yml`) intentionally pass fewer flags to ship a leaner public DB — don't align them unless deliberately changing what ships.

## other-dictionaries submodule
- To update ONE dictionary's source, recompress only that dictionary (scoped `tar` + `zstd -19` of its `source/` dir). NEVER run `scripts/compress_sources.py` for a single-dict update — it recompresses everything, and because tar embeds mtimes even unchanged sources produce new bytes (spurious diffs).

## graphify
A knowledge graph of the codebase lives at `graphify-out/` (14,254 nodes, 28,833 edges). Prefer these over grepping raw files — a scoped subgraph at ~13× fewer tokens:
```bash
graphify query "how does X work"       # BFS subgraph — use first
graphify path "DpdHeadword" "Lookup"   # shortest path between concepts
graphify explain "ProjectPaths"        # plain-language node summary
```
Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review. God nodes: `ProjectPaths`, `DpdHeadword`, `get_db_session()`, `Lookup`, `ToolKit`. After editing code run `graphify update .` (AST-only, no API cost); full rebuild is `/graphify` (costs session tokens).
