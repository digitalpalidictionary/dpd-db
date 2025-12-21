# exporter/tbw/

## Purpose & Rationale
"The Buddha's Words" (TBW) is a platform dedicated to making Early Buddhist Texts (EBTs) accessible. The `tbw/` directory provides a targeted, lightweight version of the DPD database designed for the TBW website and browser extensions (like `fdg_dpd`). It solves the problem of high-latency lookups on the web by providing compact, pre-processed JSON data that focuses on the vocabulary found in the most ancient strata of Pāḷi literature.

## Architectural Logic
This subsystem follows a "Context-Aware Micro-Index" pattern:
1.  **Filtering:** `tbw_exporter.py` limits its scope to words found in specific SuttaCentral text sets (EBTs).
2.  **Aggregation:** It combines three crucial data points for every word: its headword mapping (inflection-to-lemma), its core dictionary definition, and its compound deconstruction splits.
3.  **Compaction:** Entries are stripped of exhaustive academic metadata, focusing on clear, concise meanings and structural analysis.
4.  **Distribution:** The output is designed to be easily synced with the separate `TBW2` and `fdg_dpd` repositories.

## Relationships & Data Flow
- **Source:** Consumes `DpdHeadword` and `Lookup` (specifically deconstructor and variant data) from **db/**.
- **Consumption:** Powers the lookup features on [thebuddhaswords.net](https://thebuddhaswords.net) and related browser-based tools.
- **Integration:** The `docs/` folder within this directory contains additional integration-specific documentation for these external consumers.

## Interface
- **Export:** `uv run python exporter/tbw/tbw_exporter.py`
