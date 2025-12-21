# scripts/info/

## Purpose & Rationale
The `info/` directory provides observational and statistical tools for the project. Its rationale is to help developers and lexicographers understand the project's current state, identifying patterns across the database and measuring the scale of the corpora. It solves the problem of "blind" development by providing actionable data summaries.

## Architectural Logic
Scripts in this folder follow a "Query and Report" pattern:
1.  **Metric Calculation:** They perform targeted queries against the SQLite database or the CST/SC corpora (e.g., counting word frequencies, analyzing suffix usage).
2.  **Aggregation:** Data is grouped logically (by part of speech, by literary layer, etc.).
3.  **Reporting:** Results are typically printed to the terminal in a clean, human-readable format.

## Relationships & Data Flow
- **Input:** Reads from the live `dpd.db` and the raw text resources in **resources/**.
- **Consumption:** These reports guide decisions about which words to add, which grammatical patterns need more coverage, and how to prioritize maintenance tasks.

## Interface
- **Corpus Analysis:** `uv run python scripts/info/corpus_size.py`
- **Grammar Statistics:** `uv run python scripts/info/suffix_counter.py`
