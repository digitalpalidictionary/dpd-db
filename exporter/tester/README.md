# exporter/tester/

## Purpose & Rationale
The `tester/` directory provides a rapid prototyping environment for the Digital Pāḷi Dictionary project. Its rationale is to allow developers to experiment with new visual layouts, interactive components, and CSS styles without the overhead of rebuilding the entire massive dictionary. It solves the problem of slow iteration cycles by providing a minimal "sandbox" dictionary for development.

## Architectural Logic
This subsystem follows a "Mock-and-Render" pattern:
1.  **Isolation:** `tester.py` creates a tiny dictionary containing only one or two dummy entries (e.g., "test").
2.  **Visual Logic:** It renders these entries using local `tester.html` and `tester.css` files, allowing for immediate feedback on design changes.
3.  **Standard Export:** It utilizes the same `tools/goldendict_exporter.py` pipeline as the main project, ensuring that features tested here will function correctly in the production exporters.
4.  **Sandbox Assets:** It includes its own `fonts/` and internal `tester/` subfolder to keep experiment-specific resources isolated.

## Relationships & Data Flow
- **Input:** Usually uses mock data defined within `tester.py` or a very small subset of the DB.
- **Consumption:** Only used by developers during the design and debugging phase.
- **Output:** Produces a minimal "Tester" dictionary file for installation in GoldenDict.

## Interface
- **Export Tester:** `uv run python exporter/tester/tester.py`
- **Edit Design:** Modify `tester.html` or `tester.css` to see changes reflected in the tester dictionary.
