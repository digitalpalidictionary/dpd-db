# go_modules/

## Purpose & Rationale
`go_modules/` is the project's high-performance computing layer. It exists to solve the "Python Speed Problem" for computationally intensive tasks like large-scale compound word deconstruction and frequency analysis across massive Pāḷi corpora.

## Architectural Logic
This subsystem follows a "Specialized Service" pattern. Logic is implemented in Go for its superior execution speed and memory efficiency. These modules are not part of the main Python runtime but are designed to be run as standalone tools or subprocesses that process data and output artifacts used by the rest of the project.

## Relationships & Data Flow
- **Parallel Engine:** Works alongside the main codebase to perform the "heavy lifting."
- **Data Ingestion:** Reads raw text or DB snapshots and outputs JSON/TSV data that is subsequently ingested by the **db/** or **exporter/** modules.

## Interface
Each module is a standalone Go project.
Example: `cd go_modules/deconstructor && go run main.go`
