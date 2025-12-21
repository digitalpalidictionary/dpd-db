# exporter/sutta_central/

## Purpose & Rationale
SuttaCentral is a major Pāḷi text repository. The `sutta_central/` directory exists to provide DPD data in a specialized dictionary format required for integration into their platform. By exporting concise definitions and grammatical information as structured JSON, it allows SuttaCentral users to access DPD's dictionary data directly while reading suttas.

## Architectural Logic
This subsystem follows a "Standardized Structured Data" pattern:
1.  **Filtering:** `sutta_central_exporter.py` identifies headwords and inflected forms that are specifically found in the SuttaCentral text corpus.
2.  **Structuring:** It transforms complex dictionary entries into a simple, list-of-dictionaries JSON format containing the lemma, part of speech, meaning, and construction.
3.  **Optimization:** The data is designed to be consumed by SuttaCentral's lookup engine, prioritizing brevity and parsing speed.

## Relationships & Data Flow
- **Source:** Pulls data from `DpdHeadword` and the `Lookup` table in **db/**.
- **Linguistic Logic:** Uses `tools/cst_sc_text_sets.py` to ensure only relevant words are exported.
- **Output:** Produces a large JSON file structured for ingestion by the SuttaCentral codebase.

## Interface
- **Export:** `uv run python exporter/sutta_central/sutta_central_exporter.py`
