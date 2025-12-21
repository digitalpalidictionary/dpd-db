# exporter/kobo/

## Purpose & Rationale
The `kobo/` directory provides a specialized export path for Rakuten Kobo e-readers. Its rationale is to enable a seamless reading experience for Pāḷi texts on Kobo devices by providing a fast, native-integrated dictionary that correctly handles Pāḷi diacritics and offers essential grammatical information.

## Architectural Logic
This subsystem follows a "Template-to-Glossary" transformation pattern:
1.  **Rendering:** `kobo.py` iterates through the database, filtering for a subset of words (typically Early Buddhist Texts) to keep the dictionary size manageable.
2.  **Templating:** Uses Jinja2 (`templates/`) to render entries into simple HTML formatted specifically for the Kobo lookup engine.
3.  **Cross-Platform Logic:** Utilizes `tools/kobo_exporter.py` and the external `pyglossary` tool to package the rendered entries into the binary `.dicthtml` format used by Kobo.
4.  **Styling:** Incorporates a specialized `kobo.css` to ensure readability on e-ink screens.

## Relationships & Data Flow
- **Source:** Pulls from **db/** models, often using the `Lookup` table to resolve inflected forms back to headwords.
- **Tools:** Heavily relies on `tools/kobo_exporter.py` for the final compilation step.
- **Output:** Produces a zip file containing the Kobo-compatible dictionary files.

## Interface
- **Export:** `uv run python exporter/kobo/kobo.py`
