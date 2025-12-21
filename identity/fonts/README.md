# identity/fonts/

## Purpose & Rationale
Correct typography is essential for Pāḷi scholarship. The `fonts/` directory exists to provide the specific typefaces that support the full range of Pāḷi diacritics and Sanskrit transliteration. Its rationale is to ensure that DPD is readable and accurate on every device, solving the problem of broken character display (mojibake).

## Architectural Logic
The project currently standardizes on **Variable Fonts** (like Inter). This choice allows for a high degree of flexibility in weight and optical sizing within a single file, reducing the overall footprint of exported dictionaries and the WebApp while maintaining excellent legibility.

## Relationships & Data Flow
- **Integration:** These fonts are referenced by the project's CSS in **identity/css/**.
- **Distribution:** Exporters package these fonts into the final dictionary binaries (like GoldenDict or Kindle) to ensure they work offline.

## Interface
These are static font files. They are utilized by the project's build system and the user's browser/app.
