# scripts/bash/

## Purpose & Rationale
While individual Python scripts handle specialized tasks, the `bash/` directory provides the high-level orchestration for complex, project-wide workflows. Its rationale is to provide simple, standardized entry points for developers to perform major operations (like initial setup, full DB builds, or component regeneration) that require the coordinated execution of many different modules across the entire codebase.

## Architectural Logic
This directory follows a "Workflow Automation" pattern:
1.  **Orchestration Scripts:** Python scripts (e.g., `generate_components.py`, `initial_build_db.py`) act as the "master plan," calling individual Python and Go modules in the correct sequence.
2.  **End-to-End Chains:** These scripts handle everything from environment validation and version printing to the final packaging of build artifacts.
3.  **Error Handling:** The scripts ensure that the entire chain halts if any individual step fails, preventing data corruption or incomplete builds.

## Relationships & Data Flow
- **Control Plane:** Acts as the command center for the entire project, triggering data flow from **resources/** to **db/**, and from **db/** to **exporter/**.
- **Environment:** Ensures that the required dependencies (via `uv run`) and binaries (via `go run`) are utilized correctly during the build process.

## Interface
These are the primary entry points for developers:
- **Full Update:** `uv run python scripts/bash/generate_components.py`
- **Initial Setup:** `uv run python scripts/bash/initial_setup_run_once.py`
- **Full Build & Export:** `uv run python scripts/bash/initial_build_db_and_export_all.py`