# go_modules/tools/

## Purpose & Rationale
`go_modules/tools/` is the shared utility library for the project's Go-based subsystems. Its rationale is to provide a standardized, reusable set of functions for Pāḷi text cleaning, configuration management, and file I/O, preventing code duplication and ensuring consistent behavior across all Go modules.

## Architectural Logic
This directory follows a "Domain-Specific Utility" pattern. It provides highly focused packages for:
- **Linguistics:** `cleanMachine.go`, `runes.go`, and `strings.go` handle the specific requirements of Pāḷi character normalization.
- **Data Formats:** Optimized helpers for `tsv`, `json`, and `html` processing.
- **Environment:** `pth.go` and `configger.go` ensure Go modules use the same paths and settings as the Python codebase.
- **Observability:** `printer.go` and `tictoc.go` provide standardized logging and performance measuring.

## Relationships & Data Flow
- **Service Layer:** Acts as the internal foundation for **go_modules/deconstructor/** and **go_modules/frequency/**.
- **Abstractions:** Provides Go-native implementations of the logic found in the Python **tools/** directory to ensure results are identical across both languages.

## Interface
Intended to be imported by other Go modules.
Example: `import "github.com/digitalpalidictionary/dpd-db/go_modules/tools"`
