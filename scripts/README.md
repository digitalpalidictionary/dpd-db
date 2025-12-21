# scripts/

## Purpose & Rationale
The `scripts/` directory is the automation engine of the project. It exists to provide a clear, standardized set of entry points for common developer tasks, build processes, and maintenance routines. It encapsulates the operational workflows of the project.

## Architectural Logic
Scripts are organized by their **intent** (Action-Oriented):
- **build/:** To create or rebuild project artifacts.
- **export/:** To output the database in specific intermediate formats.
- **fix/:** To perform batch corrections on the database.
- **add/:** To find new data to add.
- **info/:** To query or report on the project state.

## Relationships & Data Flow
- **Orchestration:** Scripts import logic from **db/**, **exporter/**, and **tools/** to execute high-level workflows.
- **Integration:** They are the primary way the project interacts with CI/CD systems or local development environments.

## Interface
The interface is the CLI. Most scripts are intended to be run from the project root.
Example: `uv run python scripts/export/export_goldendict.py`
