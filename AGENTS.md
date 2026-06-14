# Project Rules

These rules are specific to the dpd-db project. Global rules (security, etc.) are in `~/.claude/CLAUDE.md`.

## Kamma Finalize
- When a thread passes review, run the full `/kamma:4-finalize` sequence immediately — do not stop after archiving; also complete the GitHub comment and reflect/lessons steps.

## Kamma Checkpoints
- Never pause a kamma thread to ask for commit permission at phase checkpoints. The user commits everything in one go at the end — checkpoint steps are report-only.

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

## Imports
- NEVER use `sys.path` hacks or manual directory traversal (e.g., `Path(__file__).resolve().parents[n]`) to handle absolute imports.
- Assume the script will be run from the project root or within a correctly configured environment where absolute imports work naturally.

## Dependencies

### uv
- Use astral uv to manage dependencies.
- Install with "uv add" not "pip install" or "uv pip install" etc.
- DO NOT run any scripts with uv UNLESS specifically asked to do so.

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
- When commenting on GitHub issues, write in the user's natural style: short, direct, lowercase sentence starts, minimal punctuation.

### Solve
- "Solve" means read the specified GitHub issue using get_issue and offer solutions. Don't think about it, don't ask questions, just read it.
- Ask the user to open the necessary files that you need.
- Is this a straightforward solution, or does it need to be solved at a higher level?
- Show code snippets of suggested changes.

## Update Gemini CLI
```bash
npm install -g @google/gemini-cli@latest
```

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
- After finishing edits to any file, ALWAYS run the same three tools the `.pre-commit-config.yaml` hook runs, in this order, plus pytest, before reporting the work as done: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright <file>`, `uv run pytest <related test paths>`.
- Do NOT skip `ruff format` — a file can pass `ruff check` and still be rewritten by the formatter, which bounces the commit.
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
This module provides colored console output with timing and TSV logging.

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

#### Logging
- If initialized with a log file path, all operations are logged to TSV format
- Log includes: timestamp, level, operation, type, message, elapsed time, count, session

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
