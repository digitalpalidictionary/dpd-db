# scripts/cl/

## Purpose & Rationale
`scripts/cl/` (Command Line) provides a set of lightweight, convenient aliases for the project's most frequent developer operations. Its rationale is to reduce "CLI friction" by providing short, memorable commands that automatically handle the complexities of finding the project root, changing directories, and invoking the correct environment (e.g., `uv run`).

## Architectural Logic
This directory follows a "Wrapper Alias" pattern:
1.  **Project Root Resolution:** Each script dynamically identifies the project's root directory based on its own location, ensuring they can be called from anywhere on the user's system (if added to the PATH).
2.  **Stateless Wrappers:** The scripts are minimal (typically 5-10 lines) and contain no business logic themselves; they purely act as shortcuts to the main entry points in `gui/`, `scripts/build/`, or `exporter/`.
3.  **Command Discovery:** The naming convention (e.g., `dpd-gui`, `dpd-build-db`) makes it easy for developers to discover available operations via tab-completion.

## Relationships & Data Flow
- **Abstraction Layer:** Sits on top of the existing **gui/**, **exporter/**, and **scripts/** subsystems.
- **Convenience:** Designed to be symbolic-linked or added to the developer's `$PATH` for instant access to the DPD toolset.

## Interface
- **Start GUI:** `scripts/cl/dpd-gui`
- **Build DB:** `scripts/cl/dpd-build-db`
- **Start WebApp:** `scripts/cl/dpd-webapp`
(etc.)
