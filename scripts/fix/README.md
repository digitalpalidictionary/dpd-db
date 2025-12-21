# scripts/fix/

## Purpose & Rationale
Data maintenance in a large dictionary is an ongoing challenge. The `fix/` directory exists to provide automated, batch-level solutions for data cleaning and normalization. Its rationale is to encapsulate common correction routines, preventing manual error and ensuring that high-level data rules (like correct character usage or family consistency) are enforced across the entire database.

## Architectural Logic
Scripts in this folder follow a "Batch Update" pattern:
1.  **Scanning:** The script iterates through a specific table or column in the database.
2.  **Detection:** Heuristic logic or regex patterns identify data that violates established standards (e.g., `extra_brackets_remover.py`).
3.  **Transformation:** In-memory cleaning of the data (e.g., `character_replacer.py`).
4.  **Persistence:** Writing the corrected data back to the database in a single transaction.
5.  **Family Logic:** Includes specialized scripts for maintaining the complex relationships in word and compound families (e.g., `family_word_update.py`).

## Relationships & Data Flow
- **Interaction:** Modifies the live `dpd.db` using **db/** models.
- **Feedback:** Often triggered by failures found in **db_tests/**.
- **System Maintenance:** Some scripts also maintain environmental files like `.gitignore`.

## Interface
Each script is a standalone tool designed for a specific fix:
- `uv run python scripts/fix/null_remover.py`
- `uv run python scripts/fix/example_1_2_cleaner.py`
(Run only when specific data cleaning is required).
