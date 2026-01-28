# exporter/webapp/

## Purpose & Rationale
`webapp/` is the project's dynamic delivery layer. It exists to provide a modern, real-time, and globally accessible interface to the DPD database. By serving the dictionary via a web application, it enables features that are difficult to achieve in static formats, such as fuzzy search, on-the-fly transliteration, and seamless audio streaming.
The webapp is currently available on https://dpdict.net

## Architectural Logic
This subsystem follows a "Dynamic SSR (Server-Side Rendering)" pattern:
1.  **Framework:** Built with FastAPI for high performance and modern asynchronous capabilities.
2.  **Request Handling:** `main.py` defines the routes and orchestrates data retrieval from the database or optimized memory caches.
3.  **Performance:** `preloads.py` prepares frequently accessed data (like headword sets and roots counts) during startup to ensure responsive search results.
4.  **Templating:** Uses Jinja2 (`templates/`) to dynamically render dictionary entries, allowing for high customization based on the user's request.
5.  **Utilities:** `toolkit.py` encapsulates common logic for formatting dictionary data specifically for the web environment.
6.  **UI Feedback:** A CSS-based spinner provides visual activity feedback on search buttons across all tabs (DPD, CST Bold Definitions, and Tipiṭaka Translations) during search operations.

## Relationships & Data Flow
- **Data Source:** Pulls live data from the SQLite database using **db/** models.
- **Static Assets:** Serves CSS, images, and client-side JS from the `static/` directory.
- **Linguistic Logic:** Utilizes **tools/** for diacritics conversion and search term normalization.
- **Deployment:** Intended to be deployed via Uvicorn/Gunicorn to the production web server (e.g., https://dpdict.net).

## Interface
- **Start Server:** `uv run uvicorn exporter.webapp.main:app --reload`
- **Generate Search Index:** `uv run python exporter/webapp/generate_search_index.py` (Run this after adding new words to the database)
- **Primary Endpoint:** Accessible via `/search` or `/word/{lemma}`.
- **API:** Provides JSON endpoints for external tools to query the database programmatically.
