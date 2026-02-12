# exporter/goldendict/

## Purpose & Rationale
`goldendict/` is the project's primary static dictionary generator. Its rationale is to provide a high-performance, offline-first visual representation of the DPD database. By pre-rendering the entire dictionary into optimized HTML and JSON, it ensures that users of GoldenDict, MDict, and other dictionary shells experience instantaneous lookups and rich formatting without needing a live database connection.

## Architectural Logic
This subsystem follows a "Pre-Rendered Component" architecture:
1.  **Orchestration:** `main.py` coordinates the parallel execution of multiple specialized exporters (DPD, EPD, Roots, Help).
2.  **Templating:** It uses the Mako template engine (`templates/`) to transform raw database records into beautiful, interactive HTML blocks.
3.  **Parallelism:** To handle the massive scale of the dictionary, `export_dpd.py` utilizes Python's multiprocessing to render entries in concurrent batches.
4.  **Minification:** Generated HTML and assets are minified to keep the final dictionary files as compact as possible.
5.  **Hybrid Interaction:** While mostly static, it integrates client-side JavaScript (`javascript/`) for interactive features like toggling conjugation tables and playing audio via the live web server.

## Relationships & Data Flow
- **Source:** Aggregates almost all data models from **db/**, including headwords, roots, families, and inflections.
- **Identity:** Pulls global CSS from **identity/** to ensure consistent branding.
- **Audio:** References the `dpd_audio` database to conditionally render play buttons.
- **Output:** Produces the source files (e.g., `.dsl`, `.txt` for MDict) that are subsequently compiled into the final dictionary binaries.

## Interface
- **Full Export:** `uv run python exporter/goldendict/main.py`