# gui2/

## Purpose & Rationale
`gui2/` represents the project's next-generation editorial interface. Its rationale is to provide a modern, reactive, and more maintainable alternative to the legacy PySimpleGUI system. By using the Flet framework (based on Flutter), it solves the problem of UI rigidity and provides a more responsive environment for the high-volume data capture and validation tasks required by DPD.

## Architectural Logic
This subsystem follows a modern "Model-View-Controller (MVC)" or "Component-Based" architecture:
1.  **Framework:** Leverages Flet to bridge Python logic with Flutter's reactive UI components.
2.  **Modular Controllers:** Specialized manager classes (e.g., `additions_manager.py`, `corrections_manager.py`) encapsulate the business logic for specific editorial workflows.
3.  **Local Persistence:** Uses the `data/` directory for fast, JSON-based workflow state, allowing for complex "multi-pass" editing without immediate database commits.
4.  **Separation of Concerns:** Clearly distinguishes between data handling (`storage/`), technical requirements (`specs/`), and the visual interface.

## Relationships & Data Flow
- **Writer:** Acts as the primary modern interface for adding and correcting data in the **db/**.
- **Validation:** Integrates deeply with **db_tests/** to ensure data quality at the point of entry.
- **Support:** Relies on **tools/** for project-wide paths and Pāḷi-specific logic.

## Interface
To start the modern GUI:
```bash
uv run flet run gui2/main.py
```
Specific maintenance utilities can be run from the `utilities/` subfolder.