# scripts/suttas/

## Purpose & Rationale
The Digital Pāḷi Dictionary is deeply integrated with canonical Buddhist literature. The `suttas/` directory exists to manage the complex mapping between dictionary headwords and their occurrences in major Pāḷi corpora (BJT, CST, SuttaCentral). It solves the problem of textual provenance by automating the extraction of sutta links, blurbs, and references.

## Architectural Logic
This subsystem follows a "Corpus Alignment" pattern, organized by source:
- **sc/ (SuttaCentral):** Synchronizes with the SuttaCentral metadata API and files, extracting sutta titles, IDs, and blurbs.
- **cst/ (CST):** Handles alignment with the Chaṭṭha Saṅgāyana Tipitaka corpus.
- **bjt/ (BJT):** Manages mappings specific to the Buddha Jayanthi Tripitaka edition.
- **dpd/ (Internal):** Centralizes the project's own sutta information logic.

## Relationships & Data Flow
- **Data Source:** Pulls raw metadata from the submodules in `resources/`.
- **Output:** Populates the `SuttaInfo` model in **db/models.py** and updates sutta reference fields in `DpdHeadword`.
- **Display:** This data powers the "Sutta" and "Source" buttons in the **Exporters** and **WebApp**.

## Interface
Each source has its own management logic. For SuttaCentral metadata:
- `uv run python scripts/suttas/sc/suttas.py`
- `uv run python scripts/suttas/sc/blurbs.py`
