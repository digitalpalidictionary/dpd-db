# exporter/

## Purpose & Rationale
The `exporter/` directory bridges the gap between the internal relational database and the diverse ecosystem of dictionary applications and devices. Its rationale is to provide a unified yet flexible pipeline for transforming the "single source of truth" (the DB) into optimized, platform-specific formats (HTML, JSON, Typst, etc.) without polluting the core data models with display logic.

## Architectural Logic
The exporters are organized by their target platform, following two main patterns:
1.  **Static Generation:** For offline apps (GoldenDict, Kindle), the system iterates through the database and pre-renders every entry using templates (Mako/Jinja2). This prioritizes end-user speed and offline availability.
2.  **Dynamic API:** For the webapp, the exporter provides a real-time interface to the data, allowing for features like search and audio streaming that are difficult to package into static files.

## Relationships & Data Flow
- **Source:** Pulls structured data from **db/**.
- **Identity:** Applies the project's visual identity (CSS/Fonts) from **identity/** during the rendering process.
- **Integration:** Provides the data schemas necessary for external integrations like **SuttaCentral** or **The Buddha's Words**.

## Interface
The primary entry points are the specialized export scripts in `scripts/export/`. Each sub-exporter (e.g., `goldendict/`) contains its own logic and templates, isolated from other export targets.