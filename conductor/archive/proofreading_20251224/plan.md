# Implementation Plan - AI-Powered Dictionary Proofreading System

## Phase 1: Setup & Data Extraction
- [x] Task: Create new track directory `conductor/tracks/proofreading_20251224/` and save `spec.md`.
- [x] Task: Create a new Python script `tools/proofreader.py` (or similar name) in the `tools/` directory (or `scripts/` if preferred for one-off tasks, but `tools/` seems more appropriate for a reusable utility).
- [x] Task: Implement `get_db_data()` function in `tools/proofreader.py` to:
    - [x] Connect to the SQLite database using `db.db_helpers.get_db_session`.
    - [x] Query `DpdHeadword` table.
    - [x] Select `id`, `lemma_1`, and `meaning_1`.
    - [x] Filter out entries with empty `meaning_1`.
    - [x] Return a list of dictionaries/objects.
- [x] Task: Create a test `tests/tools/test_proofreader_data.py` to verify data extraction works correctly (e.g., returns expected fields, handles empty DB).
- [x] Task: Conductor - User Manual Verification 'Phase 1: Setup & Data Extraction' (Protocol in workflow.md)

## Phase 2: AI Integration & Batch Processing
- [x] Task: Implement `batch_data(data, batch_size)` function to split the list of entries into chunks (default batch size 50).
- [x] Task: Implement `construct_prompt(batch)` function to format the batch into the specified prompt string.
- [x] Task: Implement `process_batch(batch)` function that:
    - [x] Instantiates `GeminiManager`.
    - [x] Sends the prompt using `gemini_manager.request`.
    - [x] Parses the JSON response from the AI.
    - [x] Handles JSON parsing errors or API failures (basic retry or skip).
- [x] Task: Create a test `tests/tools/test_proofreader_ai.py` to mock `GeminiManager` and verify batch processing logic (without making real API calls).
- [x] Task: Conductor - User Manual Verification 'Phase 2: AI Integration & Batch Processing' (Protocol in workflow.md)

## Phase 3: Output Generation & CLI
- [x] Task: Implement `save_results(results, filename)` function to write the processed data to a TSV/JSON file.
- [x] Task: Add a `main()` function to `tools/proofreader.py` to orchestrate the workflow:
    - [x] Parse command line arguments (e.g., `--limit`, `--output`).
    - [x] Call data extraction.
    - [x] Loop through batches with a progress bar (optional but good).
    - [x] Collect results.
    - [x] Save to file.
- [x] Task: Create a test `tests/tools/test_proofreader_output.py` to verify file writing.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Output Generation & CLI' (Protocol in workflow.md)
