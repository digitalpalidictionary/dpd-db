# scripts/tutorial/

## Purpose & Rationale
`scripts/tutorial/` is the onboarding layer for the project's codebase. Its rationale is to provide clear, well-commented code examples that demonstrate the "correct" way to interact with the DPD database and its subsystems. It solves the problem of a high barrier to entry by providing a safe, educational starting point for new contributors.

## Architectural Logic
This directory follows an "Annotated Example" pattern:
1.  **Code-as-Documentation:** Each script is heavily commented, explaining not just the syntax but the underlying logic of the DPD project's data models.
2.  **Standard Patterns:** Examples prioritize the use of project-standard helpers (e.g., `get_db_session`, `ProjectPaths`) to ensure developers learn the established idioms.
3.  **Core Operations:** Focuses on the most common tasks a contributor might need: searching, filtering, reading relationships (like headwords to roots), and performing safe database transactions.

## Relationships & Data Flow
- **Service Layer:** Demonstrates how to use the models in **db/models.py** and the helpers in **db/db_helpers.py**.
- **Onboarding:** Acts as a technical companion to the documentation found in the **docs/** directory.

## Interface
Developers are encouraged to run the scripts, read the console output, and then modify the filters or queries to experiment with the database.

### Examples
- **Database Search Tutorial:** `uv run python scripts/tutorial/db_search_example.py`
  - Demonstrates basic filtering, accessing related tables (roots), handling inflections, and the structure of a database commit.
- **Quick Start:** `uv run python scripts/tutorial/quick_start.py`
  - A concise example showing how to query headwords and use the `Lookup` table to find headwords and grammar information for inflected words.