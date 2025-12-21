# shared_data/abbreviations/

## Purpose & Rationale
Pāḷi scholarship uses a diverse and sometimes conflicting set of abbreviations for book titles and grammatical terms. This directory exists to solve the problem of "abbreviation ambiguity" by providing authoritative, version-controlled mappings for the most common systems (CST, PTS, etc.). Its rationale is to ensure that the dictionary can correctly parse and display references from any major edition.

## Architectural Logic
This directory follows a "Standardized Reference Mapping" pattern. It stores data in TSV format to allow for easy manual editing and Git-based tracking of changes. Each file (e.g., `abbreviations_cst.tsv`) acts as a dedicated namespace for a specific scholarly tradition.

## Relationships & Data Flow
- **Ingestion:** These files are read by `db/lookup/help_abbrev_add_to_lookup.py`.
- **Output:** They populate the `abbrev` column in the project's high-speed search index.
- **Consumption:** Every user interface (**WebApp**, **GoldenDict**) uses these mappings to provide "Click-to-Expand" abbreviation help.

## Interface
Managed via manual TSV edits or automated sync scripts in `scripts/info/`.
