# exporter/pdf/

## Purpose & Rationale
The `pdf/` directory provides a print-ready export path for the Digital Pāḷi Dictionary. Its rationale is to transform the relational database into a high-quality, professionally typeset document suitable for printing, offline reading, or distribution as a traditional book. It solves the problem of high-fidelity Pāḷi typesetting by utilizing the modern Typst engine.

## Architectural Logic
This subsystem follows a "Data-to-Typeset" transformation pattern:
1.  **Rendering:** `pdf_exporter.py` iterates through the database entries.
2.  **Markup:** It transforms dictionary data into Typst markup (`.typ`), using templates (`templates/`) to define the visual layout, columns, and typography.
3.  **Engine:** Utilizes the external Typst compiler to process the markup and images (`images/`) into the final PDF document.
4.  **Specialization:** Includes targeted scripts like `abbreviation_to_pdf.py` for generating auxiliary print materials.

## Relationships & Data Flow
- **Input:** Consumes data from the `DpdHeadword` and `DpdRoot` tables in **db/**.
- **Assets:** Pulls visual assets from the `images/` subfolder.
- **Output:** Produces high-resolution PDF files.

## Interface
- **Primary Export:** `uv run python exporter/pdf/pdf_exporter.py`
