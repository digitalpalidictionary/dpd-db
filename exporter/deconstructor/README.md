# exporter/deconstructor/

## Purpose & Rationale
Pāḷi literature is characterized by complex, often multi-word compounds (*samāsa* and *sandhi*). The `deconstructor/` exporter exists to provide a standalone reference that explicitly breaks these compounds into their constituent parts. Its rationale is to support readers by providing immediate clarity on word boundaries and components, which is often the first step in translating a complex Pāḷi sentence.

## Architectural Logic
This subsystem follows a "Specialized Component Export" pattern:
1.  **Data Retrieval:** It pulls pre-calculated compound splits from the `deconstructor` column of the `Lookup` table.
2.  **Visualization:** Uses Mako templates (`deconstructor.html`) to render the splits into a consistent, readable format.
3.  **Cross-Format Export:** Similar to the grammar dictionary, it utilizes `tools/goldendict_exporter.py` and `tools/mdict_exporter.py` to create the final binaries.
4.  **Synonym Mapping:** It includes logic to map variants and contractions, ensuring that users find the relevant deconstruction even if the search term is slightly varied.

## Relationships & Data Flow
- **Source:** Consumes data from the `Lookup` table in the database.
- **Consumption:** Provides a specialized dictionary product that can be used independently or as part of a larger dictionary collection.
- **Identity:** Shares CSS and branding with the main exporters.

## Interface
- **Export:** `uv run python exporter/deconstructor/deconstructor_exporter.py`
