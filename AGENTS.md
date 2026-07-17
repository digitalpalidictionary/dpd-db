# Project Rules

These rules are specific to the dpd-db project. Global rules (security, etc.) are in `~/.claude/CLAUDE.md`.

## Kamma Finalize
- When a thread passes review, run the full `/kamma:4-finalize` sequence immediately — do not stop after archiving; also complete the GitHub comment and reflect/lessons steps.

## Kamma Checkpoints
- Never pause a kamma thread to ask for commit permission at phase checkpoints. The user commits everything in one go at the end — checkpoint steps are report-only.

## Kamma Concurrent Threads
- Multiple kamma threads regularly run against this repo in the same working tree at once. Before staging a commit, snapshot `git status --porcelain` and cross-reference every entry against "did this thread touch this file" — stage by explicit file list, never `git add <dir>` or `git add -A`, which can silently sweep in another thread's uncommitted, unrelated changes.

## Project Overview

This project contains everything related to the Digital Pāḷi Dictionary
- Update and edit the database with `/gui2`
- Build the database `/db`
- Test the database `/db_tests`
- Export into multiple forms `/export`

## Project Specs
Detailed project documentation lives in `conductor/`:
- `conductor/product.md` — product vision, features, target audience, release schedule
- `conductor/tech-stack.md` — full technology stack and key libraries

Read the relevant spec before working in an unfamiliar area.

---

## Python Type Hints
- Please add type hints to all code, especially when it is missing in existing code.
- Use modern type hints not old type hints
  - Use `dict[str, str]` not `Dict[str, str]`
  - Use `tuple[str, str]` not `Tuple[str, str]`
  - Use `list[str]` not `List[str]`
  - Use `| None` not Optional[None]

## Use Path from Pathlib
- Use Path for anything related to filepaths, not os.

## SQLAlchemy ORM Objects
- Never mutate ORM objects unless the explicit purpose is to update, change, or delete them in the database.
- Temporary or derived values must be computed separately (e.g. a `dict` or local variable) — never written back to a tracked ORM attribute as a side-effect.

## Debugging
- Use `icecream` for debugging, not `print()`.
- Import: `from icecream import ic`
- Usage: `ic(variable_name)`

## Data Verification
- For questions about actual dictionary data (which source codes exist, how a field is populated, row counts), query the live `dpd.db` directly (`sqlite3 dpd.db` or `get_db_session`). The `db/backup_tsv/` files are regenerated backups overwritten on each db backup — not the live source of truth. Don't infer data shape from TSVs or downstream exporter code.

## Generated Data Files
- Any git-tracked data file written by code (e.g. `tools/speech_marks.json`) must be saved in canonical sort order — `pali_sort_key` for Pāḷi strings, applied to both keys and value lists. Insertion-ordered output turns every regeneration into a full-file reorder diff.

## Imports
- NEVER use `sys.path` hacks or manual directory traversal (e.g., `Path(__file__).resolve().parents[n]`) to handle absolute imports.
- Assume the script will be run from the project root or within a correctly configured environment where absolute imports work naturally.
- `.gitignore` ignores ALL `__init__.py` files repo-wide, so a package `__init__.py` re-export can never be committed. In tracked code, import new symbols from their concrete module (`from tools.cst_source.corpus_index import CstSourceIndex`), never from a package `__init__.py` you just edited.

## Go
- `go_modules/` has many `package main` directories (`frequency/`, `frequency/setup/`, `deconstructor/`, etc.). Never run `go build ./go_modules/<single-package-path>/` for a compile check — with no `-o` and exactly one main-package target, Go writes a binary to the current directory named after the package, littering the repo root with untracked multi-MB binaries. Use `go build ./go_modules/...` (compiles everything, writes no binaries because multiple main packages are targeted) or `go vet` for compile checks, or always pass `-o <scratchpad-path>` when a single package must be built.

## Codebase Sweeps / Audits
- When auditing for a pattern (e.g. "hardcoded paths", "load-all-then-filter"), do NOT anchor on a single syntactic form. The same intent hides behind many call shapes — for paths: `open(...)`, `get_db_session(Path("dpd.db"))`, `.read_text()`, `configparser.read()`, and bare module-level constants. Grep by the underlying literal (e.g. `"dpd.db"`) as well as the consuming calls, and enumerate every carrier before declaring the sweep complete. This has been missed repeatedly — look harder.
- Always sweep with `rg --hidden` — `.github/workflows/` and `.gitignore` are carriers too and a default `rg` skips them (this missed 4 files in one sweep).

## Dependencies

### uv
- Use astral uv to manage dependencies.
- Install with "uv add" not "pip install" or "uv pip install" etc.
- DO NOT run any scripts with uv UNLESS specifically asked to do so.

### Optional/transitive deps belong to their parent — don't list them as bare standalones
- If a package is only needed because another package loads it (an engine, backend, or feature plugin), prefer declaring it through the parent's extra rather than as its own top-level entry — the dep then self-documents and auto-removes if the parent is ever dropped.
- Why it matters: these are dynamic, string-keyed imports (`pd.read_excel` → `import_optional_dependency("openpyxl")`). No static tool (deptry, grep, pipdeptree) can see them, so a bare entry looks unused and gets wrongly pruned — only a test/build run reveals the break.
- EXCEPTION — keep it bare WITH an inline comment naming the owner when the extra is unusable:
  - the extra is too broad (e.g. `pandas[excel]` pulls 5 engines we never use, so we keep bare `openpyxl` for `pd.read_excel`), or
  - no extra provides it (e.g. `httpx2` is starlette's TestClient backend, but no fastapi/starlette extra ships it — their extras pull the old `httpx`).
  - In both cases the comment is mandatory so the dep never again looks orphaned.
- Before removing any dep that looks unused, confirm it is not a parent's optional engine/backend, then re-run the full test suite AND a build cycle — `uv sync` succeeding proves nothing about dynamic imports.

## Flet
- When answering questions about Flet refer to the /resources/flet-docs folder.

## Context7
Use Context7 MCP (`mcp__plugin_context7_context7__resolve-library-id` + `query-docs`) for up-to-date docs on these project libraries:
- `SQLAlchemy` — ORM, sessions, queries, relationships
- `Flet` — GUI widgets and layout
- `FastAPI` — webapp routes and middleware (`exporter/webapp/`)
- `aksharamukha` — transliteration script names and options
- `requests` — HTTP client usage

## Tree
- On a weekly basis, or anytime the project tree changes, check that the project tree matches the tree specified in @docs/technical/project_folder_structure.md

## Database model
- On a weekly basis, or anytime the database model changes, check that the database model in `db/models.py` matches the docs in `docs/technical/dpd_headwords_table.md`

## GitHub
- Unless otherwise specified the repository in question is https://github.com/digitalpalidictionary/dpd-db.
- DO NOT add or commit to GitHub, unless specifically instructed to do so.

### Commit
- Only ever commit when asked. NEVER unasked.
- "Commit" means commit the changed files using execute_command.
- Use this format, all in lowercase. #issue number area: change1, change2 . E.g. `#67 webapp: updated css, fixed overflow`
- Maximum number of characters in the first line is 72. Do not exceed that. 

### Comments
- NEVER comment on GitHub issues unless specifically asked to do so.
- When commenting on GitHub issues, write in the user's natural style: short, direct, lowercase sentence starts, minimal punctuation.

### Solve
- "Solve" means read the specified GitHub issue using get_issue and offer solutions. Don't think about it, don't ask questions, just read it.
- Ask the user to open the necessary files that you need.
- Is this a straightforward solution, or does it need to be solved at a higher level?
- Show code snippets of suggested changes.

## DPD Database Model (`db/models.py`)

Key SQLAlchemy classes and their roles:

| Class | Table | Purpose |
|---|---|---|
| `DpdHeadword` | `dpd_headwords` | Main dictionary entries — ~60 columns + many `@cached_property` helpers |
| `DpdRoot` | `dpd_roots` | Pāḷi verbal roots |
| `Lookup` | `lookup` | Fast lookup index — every inflected form → headword IDs |
| `SuttaInfo` | `sutta_info` | Sutta metadata (SC, CST, BJT links) |
| `InflectionTemplates` | `inflection_templates` | Stem/ending grids used to generate inflection tables |
| `FamilyRoot` | `family_root` | Root family groupings with HTML |
| `FamilyWord` | `family_word` | Word family groupings |
| `FamilyCompound` | `family_compound` | Compound family groupings |
| `FamilyIdiom` | `family_idiom` | Idiom groupings |
| `FamilySet` | `family_set` | Thematic set groupings |
| `BoldDefinition` | `bold_definitions` | Bold-text definitions extracted from commentaries |
| `DbInfo` | `db_info` | Key-value store for metadata and cached sets |

**`DpdHeadword` relationships:** `.rt` → `DpdRoot`, `.fr` → `FamilyRoot`, `.fw` → `FamilyWord`, `.it` → `InflectionTemplates`, `.su` → `SuttaInfo`

**JSON pack/unpack pattern:** Many string columns store JSON. Access via `foo_pack(list)` / `foo_unpack` property (e.g. `headwords_pack`, `headwords_unpack` on `Lookup`).

**Key `DpdHeadword` columns:** `id`, `lemma_1` (unique headword), `pos`, `meaning_1`, `root_key`, `family_root`, `family_compound`, `stem`, `pattern`, `inflections`, `inflections_html`, `construction`

**Empty-string gotcha:** `DpdHeadword.inflections_list_all` (and the underlying comma-splits) yields `""` entries when either inflections column is empty — always filter empty strings before using inflections as dict keys or set members in derived structures.

Full column docs: `docs/technical/dpd_headwords_table.md` | Full model: `db/models.py`

---

## Testing

### Directory Structure
- Keep the `tests/` folder tidy by mimicking the project's source folder structure.
- Example: `exporter/webapp/main.py` -> `tests/exporter/webapp/test_main.py`.
- Ensure all tests are relative to the file they are testing.

### Running Tests
- Run all tests: `uv run pytest tests/`
- Run a specific file: `uv run pytest tests/path/to/test_file.py`
- Run with durations: `uv run pytest tests/ --durations=10`
- Slow tests (those that parse large CST XML) are marked `@pytest.mark.slow` and are deselected by default (`addopts = -m 'not slow'`). Run them on demand with `uv run pytest -m slow`. New tests that parse big source files should be marked `slow`.

### Pre-commit gate
- **TOUCH A FILE = OWN ITS LINT.** The moment you edit any file, you are responsible for making it pass `ruff check` AND `pyright` cleanly — including PRE-EXISTING errors you did not introduce. The hook stages the whole file and rejects the commit on any error in it, so "it was already broken" is not an out. Fix every reported error with a real, behaviour-preserving fix (never `# noqa`). This is a repeated issue — do not skip it.
- After finishing edits to any file, ALWAYS run the same three tools the `.pre-commit-config.yaml` hook runs, in this order, plus pytest, before reporting the work as done: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright <file>`, `uv run pytest <related test paths>`.
- Do NOT skip `ruff format` — a file can pass `ruff check` and still be rewritten by the formatter, which bounces the commit.
- Exception: skip `ruff format` on `.json` fixture files — it adds trailing commas that break JSON parsing. Regenerate fixtures programmatically instead.
- The repo's pre-commit hook will reject the commit otherwise — fixing it after the fact wastes a round-trip.
- If a related test file is broken from before your changes, note it but do not silently ignore — it may mask a regression you've just introduced.
- The hook runs ruff + pyright on EVERY staged Python file (top-level `exclude:` in `.pre-commit-config.yaml` only covers `archive/`, `scripts/archive/`, `scripts/bash/`, `tools/writemdict/`). So editing any other file — even a one-line import swap — stages it and subjects its PRE-EXISTING lint errors to the gate, which blocks the commit. Before finishing, run `uv run ruff check <file>` + `uv run pyright <file>` on every touched file and fix ALL reported errors with real, behaviour-preserving fixes (narrow blind `except Exception`, direct boolean returns, `next(iter(d))`, etc.) — not `# noqa`. `gui2/` is pyright-excluded but NOT ruff-excluded, so it commonly carries pre-existing ruff violations that only surface when you touch the file.

---

## Tools/db_helpers.py
Get a database session for querying.

### Import
```python
from pathlib import Path
from db.db_helpers import get_db_session

db_path = Path("dpd.db")
db = get_db_session(db_path)
```

### Functions
- `get_db_session(db_path)` — returns a SQLAlchemy `Session`; exits with error if file not found
- `create_db_if_not_exists(db_path)` — creates the db file and tables if missing
- `create_tables(db_path)` — creates all tables (idempotent)
- `get_column_names(table_class)` — returns `list[str]` of column names for a model class

---

## Tools/configger.py
Read and write `config.ini` (project root).

### Import
```python
from tools.configger import config_read, config_update, config_test
```

### Functions
- `config_read(section, option)` — returns `str | None`
- `config_update(section, option, value)` — writes new value to `config.ini`
- `config_test(section, option, value)` — returns `bool`

### Known sections
`version`, `regenerate`, `deconstructor`, `gui`, `goldendict`, `dictionary`, `exporter`, `apis`, `anki`, `simsapa`, `tpr`

### Example
```python
api_key = config_read("apis", "openai")
config_update("regenerate", "inflections", "no")
if config_test("exporter", "make_dpd", "yes"):
    ...
```

---

## Tools/printer.py
This module provides colored console output with timing.

### Import
```python
from tools.printer import printer as pr
```

### Usage

#### Timer Methods
- `pr.tic()` - Start the main clock (class method)
- `pr.toc()` - Stop the main clock and print elapsed time (class method)
- `pr.bip()` - Start a mini clock for the current operation
- `pr.bop()` - End mini clock and return elapsed time as string
- `pr.print_bop()` - Print the elapsed time right-aligned

#### Output Methods (need ending)
These methods do NOT print a newline - follow with `pr.yes()` or `pr.no()`:
- `pr.green_tmr(message)` - Print left-aligned green message and start timer
- `pr.cyan_tmr(message)` - Print left-aligned cyan message and start timer
- `pr.white_tmr(message)` - Print indented white message and start timer

#### Output Methods (complete line)
These methods complete a line started by green_tmr/cyan_tmr/white_tmr:
- `pr.yes(message)` - Print right-aligned blue message with timing (max 8 chars)
- `pr.no(message)` - Print right-aligned red message with timing (max 8 chars)

#### Output Methods (standalone - return)
These methods print and return (no ending needed):
- `pr.yellow_title(text)` - Print bright yellow title and start timer
- `pr.green_title(message)` - Print green title and start timer
- `pr.green(message)` - Print green message
- `pr.cyan(message)` - Print cyan message
- `pr.white(message)` - Print white message
- `pr.counter(counter, total, word)` - Print progress counter with timing
- `pr.summary(key, value)` - Print key-value summary in green
- `pr.red(message)` - Print red message
- `pr.amber(message)` - Print amber message

## Pipeline Improvement

- `db_session.close()` is NOT a valid finding for short-lived build scripts. SQLAlchemy 2.0 has no `__del__`; for a script that exits after `main()`, the OS releases all connections on process exit. No resource leak. Do not flag it.

## graphify

A knowledge graph of the codebase lives at `graphify-out/` (14,254 nodes, 28,833 edges).

### Querying
```bash
graphify query "how does X work"       # BFS subgraph — use this first
graphify path "DpdHeadword" "Lookup"   # shortest path between two concepts
graphify explain "ProjectPaths"        # plain-language node summary
```
Prefer these over grepping raw files — they return a scoped subgraph at ~13× fewer tokens.

Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review.

### Key god nodes (highest connectivity)
`ProjectPaths` · `DpdHeadword` · `get_db_session()` · `Lookup` · `ToolKit`

### Keeping it current
After editing code, run (AST-only, no API cost):
```bash
graphify update .
```

To fully rebuild from scratch (requires Claude Code session tokens):
```bash
/graphify
```

## Mobile DB export flags
- The local justfile recipes `export-mobile` (dpd-db) and `build-db` (dpd-flutter-app) MUST pass the same `mobile_exporter.py` flags (`--cone --peu --wordnet`) so a local build equals the packaged DB. Keep both in sync when changing flags.
- The CI release workflows (`mobile_release.yml`, `draft_release.yml`) intentionally pass fewer flags to ship a leaner public DB — do not align them to the full local set unless deliberately changing what the public release ships.

## other-dictionaries submodule
- To update ONE dictionary's source, recompress only that dictionary (scoped `tar` + `zstd -19` of its `source/` dir). NEVER run `scripts/compress_sources.py` for a single-dict update — it recompresses every dictionary, and because tar embeds mtimes, even unchanged sources produce new `.tar.zst` bytes (spurious apte/cone/etc. diffs).

## Performance Work
- Before implementing any optimization spec: re-derive its numbers from the actual profiling log (`logs/makedict_*.html`) and benchmark the claimed mechanism on a throwaway copy of `dpd.db` (`cp dpd.db /tmp/...`). Two of five premises in one thread were wrong, one destructively so.
- The recurring makedict bottleneck is ORM loops over large tables (load-all + per-row mutate + commit). Replace with a single `executemany` on the session's own connection — pattern: `tools/lookup_sync.py:_raw_sql_sync`. Never `INSERT OR REPLACE` on `lookup` (blanks the other 16 columns); use `ON CONFLICT ... DO UPDATE SET <col> = excluded.<col>`.
