# Tech Notes

## Tools & Platforms
This project is primarily a Python 3.13 codebase managed with `uv`. It uses SQLite as the main database and SQLAlchemy for database access and modeling. It also includes Go modules for performance-sensitive tasks, Flet for the contributor GUI, FastAPI and Uvicorn for web-facing services, and multiple exporter pipelines for web, mobile, desktop dictionary, and document outputs. Some gui2 AI workflows now also use locally authenticated CLI wrappers such as `codex` and `claude` through the shared AI manager.

## Who This Is For
These notes are for internal contributors and editors maintaining dictionary data, the database build process, tests, and release exports.

## Constraints
- Work needs to fit the existing Python 3.13, `uv`, SQLite, and SQLAlchemy stack.
- GUI-based data entry, database generation, testing, and exporter flows all need to stay reliable for contributors.
- Project conventions require modern type hints, `pathlib.Path` for file paths, and avoiding `sys.path` import hacks.
- The repository already contains multiple output targets, so changes should preserve compatibility with downstream exporters and integrations.
- This is an existing Git-managed project, so setup should work with the current repository structure and conventions rather than replacing them.
- `db/db_helpers.get_db_session()` reuses one cached Engine per db path (NullPool, fork-PID guard); gui2 derives all full-table headword data from `DatabaseManager.load_corpus()` and marks it stale via `mark_corpus_stale()` after any headword write — don't reintroduce per-call engines or direct `.all()` loads of `DpdHeadword` in gui2.
- Flet 0.28.3 (pinned, `flet[all]==0.28.3`) exposes no cursor-position/selection API on `ft.TextField` — putting the caret at the end of a pre-filled field relies on calling `.focus()` after the value is set, not a real cursor setter. There are also no per-dialog keyboard events: dialog-scoped keys (e.g. Enter = submit) must hook `page.on_keyboard_event` with a save/restore wrapper (see the EG popup in `gui2/pass2_add_view.py`).

## Resources
- PDF export requires the `typst` CLI on PATH (>= 0.14 for
  `--no-pdf-tags`); CI installs the musl binary in the workflow. The
  exporter compiles in ~31 memory-bounded chunks (~2 GB per typst
  subprocess, ~3.5 GB total peak) and merges with pypdf — a single
  compile would need ~29 GB (typst holds ~2 MB per laid-out page).
  Body-level `#set par/page` rules in rendered typst data must stay
  on one line so chunk state replay captures them.
- Mobile DB export requires dictionary sources to be materialized first:
  `cd resources/other-dictionaries && uv run python scripts/prepare_sources.py`
  (decompresses tracked archives, builds MW fresh from Cologne with tracked
  `mwweb1.zip` fallback). `mobile_exporter.py` hard-fails if sources are missing.
- `README.md` and `CONTRIBUTING.md`
- `conductor/product.md` and `conductor/tech-stack.md`
- `docs/technical/` for database and project structure documentation
- `db/`, `gui2/`, `exporter/`, `tests/`, and `scripts/` as the main implementation areas
- `resources/flet-docs/` for Flet reference material
- Slob export in CI relies on `PyICU` and ICU system libraries

## What The Output Looks Like
The project outputs updated dictionary data, a generated and tested SQLite database, and export artifacts in multiple formats for downstream apps, websites, offline dictionaries, and related release channels.
