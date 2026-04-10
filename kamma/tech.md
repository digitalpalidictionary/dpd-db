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

## Resources
- `README.md` and `CONTRIBUTING.md`
- `conductor/product.md` and `conductor/tech-stack.md`
- `docs/technical/` for database and project structure documentation
- `db/`, `gui2/`, `exporter/`, `tests/`, and `scripts/` as the main implementation areas
- `resources/flet-docs/` for Flet reference material

## What The Output Looks Like
The project outputs updated dictionary data, a generated and tested SQLite database, and export artifacts in multiple formats for downstream apps, websites, offline dictionaries, and related release channels.
