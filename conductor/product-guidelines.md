# Product Guidelines

## Design Principles
- **Clarity and Precision:** Dictionary definitions and grammatical info must be easy to read and technically accurate.
- **Consistency:** Use consistent terminology and formatting across all platforms (Web, GoldenDict, etc.).
- **CSS Single Source of Truth:** All styles MUST originate from `identity/css/`. Never modify CSS files directly in `exporter/` or `webapp/` subdirectories; use `tools/css_manager.py` to propagate changes from the source.
- **Accessibility:** Ensure the content into accessible to users with different technical abilities and scripts.

## Visual Aesthetic: Minimalist and Functional
- **Information Density Management:** Design is focused on presenting dense tabular data in a readable manner, enabling users to extract specific information quickly from an overload of data.
- **Progressive Disclosure:** Use buttons and tables to hide complex or secondary data, showing it only when requested to maintain a clean interface.
- **Cross-Platform Legibility:** Prioritize simple layouts and high-contrast text to ensure consistent readability across web, mobile, and e-reader devices.

## Communication Style
- **Technical Accuracy:** Use standard linguistic and Buddhist terminology consistently.
- **Directness:** Present information without unnecessary ornamentation, focusing on the utility of the dictionary data.
