# Project Rules

These rules are specific to the dpd-db project. Global rules (security, etc.) are in `~/.claude/CLAUDE.md`.

## Project Overview

This project converts Mako templates to Jinja2 templates for the Digital Pali Dictionary.

## Python Type Hints
- Please add type hints to all code, especially when it is missing in existing code.
- Use modern type hints not old type hints
  - Use `dict[str, str]` not `Dict[str, str]`
  - Use `tuple[str, str]` not `Tuple[str, str]`
  - Use `list[str]` not `List[str]`
  - Use `| None` not Optional[None]

## Use Path from Pathlib
- Use Path for anything related to filepaths, not os.

## Debugging
- Use `icecream` for debugging, not `print()`.
- Import: `from icecream import ic`
- Usage: `ic(variable_name)`

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
- `pr.green(message)` - Print left-aligned green message and start timer
- `pr.cyan(message)` - Print left-aligned cyan message and start timer
- `pr.white(message)` - Print indented white message and start timer

#### Output Methods (complete line)
These methods complete a line started by green/cyan/white:
- `pr.yes(message)` - Print right-aligned blue message with timing (max 8 chars)
- `pr.no(message)` - Print right-aligned red message with timing (max 8 chars)

#### Output Methods (standalone - return)
These methods print and return (no ending needed):
- `pr.title(text)` - Print bright yellow title and start timer
- `pr.green_title(message)` - Print green title and start timer
- `pr.counter(counter, total, word)` - Print progress counter with timing
- `pr.summary(key, value)` - Print key-value summary in green
- `pr.red(message)` - Print red message
- `pr.amber(message)` - Print amber message

#### Logging
- If initialized with a log file path, all operations are logged to TSV format
- Log includes: timestamp, level, operation, type, message, elapsed time, count, session
