# exporter/tpr/

## Purpose & Rationale
The `tpr/` directory provides a specialized export path for the Tipitaka Pali Reader (TPR) app. Its rationale is to enable mobile and desktop readers using TPR to benefit from DPD's dictionary data. It solves the problem of cross-app compatibility by transforming the complex DPD database into the specific SQLite/JSON formats required by the TPR ecosystem.

## Architectural Logic
This subsystem follows an "Aggregated Component Export" pattern:
1.  **Rendering:** `tpr_exporter.py` uses Mako templates (sharing some logic with the GoldenDict exporter) to generate simplified HTML definitions for every headword, specifically the overview and grammar tab.
2.  **Mapping:** It creates specialized CSV/JSON lists for inflection-to-lemma (i2h) mapping and compound deconstruction splits.
3.  **Compaction:** The data is optimized for the constrained resources of mobile devices, focusing on speed and essential content.
4.  **Packaging:** It bundles these components into structured zip files and SQLite databases ready for distribution via the TPR app's update system.

## Relationships & Data Flow
- **Source:** Consumes `DpdHeadword`, `DpdRoot`, and `Lookup` data from **db/**.
- **Consumption:** Directly powers the lookup and dictionary features within the Tipitaka Pali Reader applications.
- **Artifacts:** Output files are stored in the `output/` subfolder before distribution.

## Interface
- **Export All:** `uv run python exporter/tpr/tpr_exporter.py`
