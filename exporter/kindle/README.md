# exporter/kindle/

## Purpose & Rationale
The `kindle/` directory provides a specialized export path for Amazon Kindle e-readers. Its rationale is to solve the problem of reading Pāḷi texts on Kindle by providing a lightweight, fast, and correctly formatted dictionary that integrates directly with the Kindle OS's lookup feature.

## Architectural Logic
This subsystem follows an "EPUB-to-MOBI" transformation pattern:
1.  **Rendering:** `kindle_exporter.py` iterates through the database and uses Jinja2 templates (`templates/`) to generate the HTML and metadata files required for a Kindle dictionary.

    **Entries are keyed so every form reaches every sense it has.** A Kindle index term resolves to exactly *one* entry, so labelling entries with `lemma_clean` made all 13 `uttara` homonyms claim one label and left 12 unreachable (8% of the dictionary). Instead: each headword gets one full entry labelled `lemma_1` (unique); each *ambiguous* form gets an entry listing exactly the headwords `Lookup.headwords_unpack` names, each linking to its full entry; unambiguous forms are plain `<idx:iform>` aliases on their owner. Devanāgarī, Sinhala and Thai spellings attach as aliases from `Lookup`'s own script columns, so one dictionary recognises all four scripts.

    Known firmware limitation: the sense links are not tappable inside the lookup popup, but are when the dictionary is opened as a book.

    **Styling the MOBI: CSS does not reach it.** kindling strips every stylesheet rule, `class` and `style` attribute out of the MOBI — verified by rendering a minimal entry, where `<p class="body-space">` came out as a bare `<p>`. Inline `style`, `<span style>` and `<div style>` are all dropped too. What survives is the legacy MOBI markup: `<blockquote>` and the `width` / `height` / `align` attributes. The hanging indent on sense lines is built from those — `<blockquote>` for the left margin, `width="-1em"` to pull the first line back out flush with the headword. `dpd_kindle.css` is still worth keeping because the ePub *does* use it, but any change there has no effect on the Kindle dictionary.
2.  **Structuring:** It organizes these files into a standard EPUB structure (`epub/`), including cover art and internal stylesheets.
3.  **Compilation:** It utilizes the `kindling-cli` tool to compile the OPF into the final `.mobi` format recognized by Kindle devices. The binary is not committed. CI downloads and checksums the pinned release; see the *Install kindling* step in `.github/workflows/draft_release.yml` for the version and SHA-256. Locally, put an executable `kindling-cli` at `exporter/kindle/kindling-cli`.
4.  **Optimization:** The content is heavily stripped down compared to the GoldenDict version to ensure it remains performant on Kindle's limited hardware.

## Relationships & Data Flow
- **Source:** Extracts a curated subset of data from the **db/** models.
- **Identity:** Uses a simplified version of the project's CSS optimized for e-ink displays.
- **Output:** Produces a single dictionary binary file ready for side-loading onto Kindle devices.

## Interface
- **Export:** `just export-kindle`
- **Manual Adjustments:** Cover and metadata can be adjusted in the `cover/` and `epub/` directories respectively.
