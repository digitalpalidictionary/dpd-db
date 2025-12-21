# gui/ & gui2/

## Purpose & Rationale
These directories provide the human interface for the dictionary's data entry and management. They exist to simplify the complex task of capturing Pāḷi lexicographical data, providing validation, auto-suggestion, and visualization tools that would be impossible in a raw database environment.

## Architectural Logic
The project is currently in a transition phase:
- **gui/ (Legacy):** Built with PySimpleGUI. It is monolithic and stable, handling the bulk of existing data capture workflows.
- **gui2/ (Modern):** Built with Flet. It uses a more modular, component-based architecture. The goal is to provide a more responsive and maintainable interface, gradually replacing legacy features.

## Relationships & Data Flow
- **Interaction:** These are the primary "writers" to the **db/**.
- **Validation:** They integrate with **db_tests/** to provide real-time feedback to editors about data quality.
- **Support:** They use **tools/** for diacritics management and linguistic sorting.

## Interface
The GUIs are started via their respective entry points:
- Legacy: `uv run python gui/gui_main.py`
- Modern: `uv run flet run gui2/main.py`