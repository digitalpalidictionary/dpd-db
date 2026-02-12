# exporter/kindle/

## Purpose & Rationale
The `kindle/` directory provides a specialized export path for Amazon Kindle e-readers. Its rationale is to solve the problem of reading Pāḷi texts on Kindle by providing a lightweight, fast, and correctly formatted dictionary that integrates directly with the Kindle OS's lookup feature.

## Architectural Logic
This subsystem follows an "EPUB-to-MOBI" transformation pattern:
1.  **Rendering:** `kindle_exporter.py` iterates through the database and uses specialized Mako templates (`templates/`) to generate the HTML and metadata files required for a Kindle dictionary.
2.  **Structuring:** It organizes these files into a standard EPUB structure (`epub/`), including cover art and internal stylesheets.
3.  **Compilation:** It utilizes the `kindlegen` tool to compile the EPUB into the final `.mobi` or `.azw3` format recognized by Kindle devices.
4.  **Optimization:** The content is heavily stripped down compared to the GoldenDict version to ensure it remains performant on Kindle's limited hardware.

## Relationships & Data Flow
- **Source:** Extracts a curated subset of data from the **db/** models.
- **Identity:** Uses a simplified version of the project's CSS optimized for e-ink displays.
- **Output:** Produces a single dictionary binary file ready for side-loading onto Kindle devices.

## Interface
- **Export:** `uv run python exporter/kindle/kindle_exporter.py`
- **Manual Adjustments:** Cover and metadata can be adjusted in the `cover/` and `epub/` directories respectively.
