# shared_data/frequency/

## Purpose & Rationale
`shared_data/frequency/` is the project's statistical reservoir. Its rationale is to provide pre-calculated word frequency and distribution data across multiple Pāḷi corpora (BJT, CST, SuttaCentral, Syāmaraṭṭha). This data allows the dictionary to prioritize common words and provides scholars with essential information about a word's rarity or textual distribution.

## Architectural Logic
This directory follows a "Pre-Calculated Static Index" pattern. It stores data in JSON format for high-speed programmatic access. Each corpus is represented by three types of data:
1.  **Word Frequencies (`..._freq.json`):** Total count of every unique word-form in that corpus.
2.  **File Distribution (`..._file_freq.json`):** Breakdown of word counts per individual text or book.
3.  **Unique Wordlists (`..._wordlist.json`):** Optimized sets of unique forms for fast set operations.

## Relationships & Data Flow
- **Generation:** These files are produced by the high-performance **go_modules/frequency/** engine.
- **Consumption:** Integrated into the main database by `scripts/build/ebt_counter.py` and used by the **WebApp** to display frequency charts.
- **Inward Flow:** Also used by the **deconstructor** to prioritize splits that consist of common Pāḷi words.

## Interface
Read-only data files. They are automatically updated whenever the full frequency analysis suite is run.
