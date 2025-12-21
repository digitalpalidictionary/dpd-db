# tools/

## Purpose & Rationale
The `tools/` directory is the project's utility layer. It exists to centralize shared logic and prevent code duplication across the database, GUI, and exporter subsystems. It handles the "dirty work" of Pāḷi text processing, AI interaction, and environment configuration.

## Architectural Logic
Tools are organized into stateless modules that follow a "Utility Library" pattern. They are designed to be imported and used as needed, rather than being standalone entry points (though many include `__main__` blocks for testing). The logic is categorized by its domain: linguistic (sorting/diacritics), data (caching/TSV), or system (paths/config).

## Relationships & Data Flow
- **Service Layer:** Acts as a helper to every other directory in the project (**db/**, **gui/**, **exporter/**, **scripts/**).
- **Abstractions:** Provides high-level abstractions for complex tasks like "sort these words correctly according to the Pāḷi alphabet."

## Interface
Developers interact with this subsystem through standard Python imports.
Example: `from tools.pali_sort_key import pali_sort_key`
