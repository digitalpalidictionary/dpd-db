# Exporters

This directory contains logic for exporting the DPD database into various formats and platforms.

## Core Architectures

The DPD project utilizes two primary export mechanisms for its main dictionary products.

### 1. Webapp Exporter (`exporter/webapp`)
*   **Type:** Dynamic, Server-Side Rendering (SSR) & API.
*   **Technology:** FastAPI (Python).
*   **Architecture:** 
    *   Requests are handled by `main.py`.
    *   Data is fetched from the database in real-time or from preloaded caches (`preloads.py`).
    *   Templates (`templates/`) are rendered on-the-fly using Jinja2/Mako.
    *   Static assets (`static/`) including CSS and JS are served directly.
    *   **Audio:** Audio is served via an API endpoint that streams the file or redirects to a static resource.
*   **Key Files:**
    *   `main.py`: Entry point and route definitions.
    *   `templates/dpd_headword.html`: The main presentation template.

### 2. GoldenDict Exporter (`exporter/goldendict`)
*   **Type:** Static Content Generation.
*   **Technology:** Python Script generating HTML/JSON.
*   **Architecture:**
    *   The export process (`main.py` -> `export_dpd.py`) iterates through the entire dictionary database.
    *   For each entry, it generates a pre-rendered HTML block using Mako templates (`templates/`).
    *   These HTML blocks are combined with shared CSS and JavaScript (`javascript/`) to create a dictionary file (e.g., `.dsl` or specialized format for GoldenDict).
    *   **Audio:** Since GoldenDict is often used offline, audio is typically packaged or linked. In this implementation, we are using the `playAudio` JS function to fetch audio from the Webapp's live server, hybridizing the static offline content with online resources. **To ensure a high-quality user experience, the play button is only rendered if a corresponding entry exists in the `dpd_audio` database.**
*   **Key Files:**
    *   `export_dpd.py`: Core logic for iterating words and rendering templates.
    *   `templates/dpd_button_box.html`: Component template for action buttons (now including Play).
    *   `javascript/main.js`: Client-side logic packed into the dictionary, handling user interactions like the Play button.

## Other Exporters

In addition to the main dictionary, the project exports data for specific devices, platforms, and auxiliary tools.

- **Deconstructor** (`exporter/deconstructor`): Exports the compound word deconstruction data for GoldenDict and MDict.
- **Grammar Dictionary** (`exporter/grammar_dict`): Exports the DPD Grammar dictionary to GoldenDict and MDict.
- **Kindle** (`exporter/kindle`): Generates a lightweight version of DPD formatted for Kindle e-readers.
- **Kobo** (`exporter/kobo`): Generates a lightweight version of DPD formatted for Kobo e-readers.
- **MCP Server** (`exporter/mcp_server`): Model Context Protocol server implementation.
- **Other Dictionaries** (`exporter/other_dictionaries`): Exports other Pāḷi and Sanskrit dictionaries to GoldenDict and MDict.
- **PDF** (`exporter/pdf`): Generates PDF versions of the dictionary using Typst.
- **Share** (`exporter/share`): Shared resources or exports.
- **Sinhala** (`exporter/sinhala`): Exports a Sinhala version of the dictionary.
- **Sutta Central** (`exporter/sutta_central`): Exports data for integration with SuttaCentral.
- **The Buddha's Words** (`exporter/tbw`): Exports a lightweight version of DPD for "The Buddha's Words" website.
- **Tipitaka Pali Reader** (`exporter/tpr`): Exports DPD grammar and deconstructor data for the Tipitaka Pali Reader app.
- **Text** (`exporter/txt`): Exports data in plain text formats.
- **Variants** (`exporter/variants`): Exports variant readings.
- **Word Trees** (`exporter/word_trees`): Exports word tree data.

## Shared Resources
*   All exporters rely on the common data models in `db/models.py`.
*   Many use `identity/css/dpd.css` for consistent styling.