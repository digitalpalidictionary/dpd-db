# exporter/variants/

## Purpose & Rationale
Manuscript variations and spelling differences are common in Pāḷi literature. The `variants/` directory exists to provide a standalone reference that helps users navigate these differences. Its rationale is to ensure that even if a user searches for a variant spelling found in a specific edition (like BJT or PTS), the dictionary can correctly redirect them to the canonical entry or explain the variation.

## Architectural Logic
This subsystem follows an "Alias and Reference" pattern:
1.  **Data Ingestion:** It pulls pre-calculated variant mappings from the `variant` column of the `Lookup` table.
2.  **Normalization:** Logic within `variants_exporter.py` cleans and categorizes these variants (e.g., handling the specific formatting used in the Buddha Jayanti Tipiṭaka).
3.  **Synonym Generation:** It automatically generates synonym lists so that every variant form becomes a searchable key in the final dictionary binary.
4.  **Standard Export:** Uses the common project pipeline to produce GoldenDict and MDict files.

## Relationships & Data Flow
- **Source:** Consumes data from the `Lookup` table in the database.
- **Consumption:** Integrated by users as a supporting dictionary to improve the overall "search hit rate" of their dictionary setup.
- **Tools:** Shares rendering and export utilities with the main project.

## Interface
- **Export:** `uv run python exporter/variants/variants_exporter.py`
