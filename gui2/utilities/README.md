# gui2/utilities/

## Purpose & Rationale
While the main `gui2/` system provides a general interface for dictionary management, the `utilities/` directory exists to provide highly specialized "Micro-Tools" for specific editorial tasks. Its rationale is to encapsulate complex logic (like identifying words with existing examples across multiple columns) into standalone, task-oriented Flet applications.

## Architectural Logic
This directory follows a "Specialized Utility Application" pattern:
1.  **Isolation:** Each script is a self-contained Flet application with its own Controller, UI, and Data logic.
2.  **Task Focus:** Tools are designed for one-off or repetitive maintenance tasks that would clutter the main GUI interface (e.g., `find_words_with_examples.py` or complex sandhi find-and-replace).
3.  **Modern UI:** Leverages the Flet framework to provide a responsive and native-feeling interface for these specialized operations.

## Relationships & Data Flow
- **Input:** Directly queries the database using **db/** models.
- **Integration:** Often interacts with external tools (like GoldenDict) to provide a rich context for the editor during the task.
- **Support:** Pulls from **tools/** for alphabet and path definitions.

## Interface
Each utility can be run individually:
- `uv run flet run gui2/utilities/find_words_with_examples.py`
- `uv run flet run gui2/utilities/sandhi_contraction_find_replace_gui.py`
