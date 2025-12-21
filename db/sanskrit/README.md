# db/sanskrit/

## Purpose & Rationale
Pāḷi is an Indo-Aryan language closely related to Sanskrit. The `sanskrit/` directory exists to provide etymological and comparative context for Pāḷi entries by mapping them to their closest Sanskrit cognates. This information is crucial for scholars and provides a deeper understanding of the linguistic development of Pāḷi terms.

## Architectural Logic
This directory follows a "Comparative Data Maintenance" pattern. It stores manually curated mappings and style guides that ensure consistency when identifying and recording Sanskrit cognates. The rationale is to maintain a high-quality link between the two languages that can be displayed alongside the Pāḷi definitions.

## Relationships & Data Flow
- **Input:** Relies on expert manual curation, often tracked in external spreadsheets (e.g., `DPD Sanskrit Updates v1.xlsx`) or TSVs.
- **Output:** Populates the `sanskrit` column in the `DpdHeadword` and `DpdRoot` tables in the database.
- **Standards:** The `sanskrit_style_guide.md` ensures that transliteration and citation of Sanskrit terms remain uniform across the project.

## Interface
This directory is primarily a data and guidelines repository. Updates are typically performed by importing the curated TSVs or Excel files into the database via scripts in `scripts/add/` or specialized maintenance routines.
