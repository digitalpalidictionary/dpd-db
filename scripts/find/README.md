# scripts/find/

## Purpose & Rationale
`scripts/find/` is the project's analysis and discovery engine. Its rationale is to help lexicographers and developers identify the most impactful areas for improvement. By scanning the database and Tipitaka corpora for gaps (missing words, missing examples, or linguistic patterns), it transforms raw data into a prioritized task list. It solves the problem of "where to work next" by highlighting the most common missing terms and logical errors.

## Architectural Logic
Scripts in this folder follow a "Gap Analysis and Discovery" pattern:
1.  **Corpus Scanning:** They frequently compare the dictionary database against large Pāḷi corpora to find "unrecognized" words (e.g., `most_common_missing_word_finder.py`).
2.  **Pattern Matching:** They search for specific linguistic or structural features (prepositions, root verbs, deconstruction errors).
3.  **Heuristic Prioritization:** `low_hanging_fruit_finder.py` uses metrics like word frequency or data completeness to identify tasks that provide maximum benefit for minimal effort.
4.  **Reporting:** Results are typically output as TSV files (e.g., `most_common_missing_words.tsv`) or terminal reports that inform the project's next developmental steps.

## Relationships & Data Flow
- **Input:** Consumes data from the live `dpd.db` and the raw corpora in **resources/**.
- **Output:** Generates research artifacts stored within this directory or in **shared_data/**.
- **Cycle:** The findings here often directly trigger the addition of new words via **scripts/add/** or data corrections via **scripts/fix/**.

## Interface
Each script is a standalone discovery tool:
- **Find missing words:** `uv run python scripts/find/most_common_missing_word_finder.py`
- **Analyze examples:** `uv run python scripts/find/word_without_examples_analyser.py`
