# docs/

## Purpose & Rationale
The `docs/` directory is the "Public Mind" of the project. It exists to transform the project's internal knowledge into an accessible, searchable format for users, scholars, and new developers. It solves the problem of knowledge silos by providing a centralized documentation website.

## Architectural Logic
The documentation follows a "Doc-as-Code" pattern:
- **Source:** Markdown files organized by topic (install, features, technical).
- **Structure:** Managed by the root `mkdocs.yaml` file.
- **Visuals:** Separated into `assets/` and `pics/` to keep text content clean.

## Relationships & Data Flow
- **Presentation:** Uses the visual identity from **identity/**.
- **Synchronization:** Some pages are automatically updated by scripts in **scripts/info/** to ensure the documentation reflects the actual state of the database (e.g., abbreviations).

## Interface
Committing changes in this directory automatically triggers a rebuild process of the docs website, which is a GitHub page. 
Users interact with this via the generated website. Developers interact with it by editing Markdown files and using MkDocs:
- Preview: `uv run mkdocs serve`
- Build: `uv run mkdocs build`

