# shared_data/help/

## Purpose & Rationale
The `help/` directory stores the descriptive content that guides users through the dictionary. Its rationale is to provide a central, easily editable location for metadata that isn't part of the core linguistic data but is essential for usability, including help text, bibliographic references, and acknowledgments.

## Architectural Logic
This directory follows a "Metadata Content Management" pattern. It uses TSVs to store structured text blocks that can be easily translated or updated without modifying code.
- **`help.tsv`:** Contextual help strings for the user interface.
- **`bibliography.tsv`:** Authoritative source list for citations.
- **`thanks.tsv`:** Acknowledgment of contributors and organizations.

## Relationships & Data Flow
- **Ingestion:** These files are consolidated into the searchable index by `db/lookup/help_abbrev_add_to_lookup.py`.
- **Consumption:** The **WebApp** and **GoldenDict** exports pull these strings to display the "Help" and "About" sections.

## Interface
Managed via manual TSV edits.
