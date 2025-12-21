# exporter/sinhala/

## Purpose & Rationale
`exporter/sinhala/` provides a localized export path specifically for the Sinhala-speaking community. Its rationale is to transform the core DPD data and the specialized translations from the `db/sinhala/` subsystem into a standalone dictionary format suitable for GoldenDict and MDict. It ensures that the Pāḷi scholarship within DPD is accessible to those who prefer to study via Sinhala.

## Architectural Logic
This subsystem follows a "Localized Visual Representation" pattern:
1.  **Data Ingestion:** Pulls headword data and their associated `si` (Sinhala) models from the database.
2.  **Templating:** Uses a specialized Jinja2 template (`dpd_sinhala_template.html`) that prioritizes Sinhala definitions and correctly handles Sinhala script rendering.
3.  **Cross-Format Export:** Utilizes the project's standard export tools to generate binaries for both GoldenDict and MDict.
4.  **Styling:** Incorporates `dpd_sinhala.css` to handle the specific typographical requirements of the Sinhala script.

## Relationships & Data Flow
- **Source:** Pulls from `DpdHeadword` and `Sinhala` tables in **db/**.
- **Consumption:** Provides a localized dictionary product for the Sri Lankan and Sinhala-speaking diaspora.
- **Tools:** Relies on `tools/goldendict_exporter.py` and `tools/mdict_exporter.py` for final artifact generation.

## Interface
- **Export:** `uv run python exporter/sinhala/dpd_sinhala_exporter.py`
