# go_modules/deconstructor/

## Purpose & Rationale
The Pāḷi language features massive compound words that can be split in millions of mathematically possible ways. The `deconstructor/` module exists to solve this problem with high performance. Written in Go, it can analyze the entire Tipitaka corpus in a fraction of the time it would take in Python, identifying the most likely word boundaries based on established sandhi rules and known vocabulary.

## Architectural Logic
This module follows a "Heuristic Splitter" architecture:
1.  **Importers:** Ingests the dictionary data and sandhi rules from the **shared_data/** and **db/** directories.
2.  **Splitters:** Specialized Go logic (`splitters/`) performs recursive splitting of compounds, applying phonetic rules to identify valid sub-words.
3.  **Data Models (`data/`):** Efficient Go-native data structures for fast word lookup and rule application.
4.  **Batch Processing:** The `main.go` entry point orchestrates the processing of millions of unique word-forms concurrently.

## Relationships & Data Flow
- **Input:** Consumes rules and verified splits from **shared_data/deconstructor/**.
- **Output:** Produces optimized JSON/TSV artifacts in `output/` that are subsequently ingested by the **exporter/deconstructor/** subsystem.
- **Service:** Acts as the computational "heavy lifter" for the project's sandhi and samāsa analysis.

## Interface
- **Run Full Analysis:** `go run go_modules/deconstructor/main.go`
- **Documentation:** See `deconstructor.md` for detailed algorithm logic.
