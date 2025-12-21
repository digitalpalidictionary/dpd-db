# go_modules/frequency/

## Purpose & Rationale
Analyzing word frequencies across massive Pāḷi corpora is a "Big Data" problem that requires high speed and memory efficiency. The `frequency/` module exists to perform this analysis, scanning millions of words in seconds to generate the statistical maps that inform the dictionary's prioritizing and scholarly value.

## Architectural Logic
This module follows a "Concurrent Corpus Scanner" architecture:
1.  **Scanning:** It reads multiple Pāḷi corpora concurrently, tokenizing and normalizing word-forms on the fly.
2.  **Aggregation:** Uses Go's highly optimized map structures to count occurrences and track distribution across individual files (`file_maps/`).
3.  **Visualization (`gradient/`):** Includes logic for calculating the "heat maps" or gradients that the WebApp uses to visually represent word frequency.
4.  **Setup & Templating:** Manages the configuration of corpus paths (`setup/`) and the generation of JSON artifacts for consumption by the main codebase.

## Relationships & Data Flow
- **Input:** Reads raw Pāḷi text from the submodules in **resources/**.
- **Output:** Produces the comprehensive JSON datasets in **shared_data/frequency/**.
- **Service:** Provides the fundamental statistics that power the project's frequency charts and "most common word" lists.

## Interface
- **Run Frequency Suite:** `go run go_modules/frequency/main.go`
