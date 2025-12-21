# identity/css/

## Purpose & Rationale
`identity/css/` is the project's visual master-template. Its rationale is to provide a single, version-controlled source for all styling rules used across the DPD ecosystem. By centralizing CSS here, we ensure that a change to a color or font choice automatically propagates to the WebApp, GoldenDict, and other exported formats, maintaining a unified brand identity.

## Architectural Logic
The CSS is structured using a "Variable-First" and "Component-Based" pattern:
1.  **Variables (`dpd-variables.css`):** Defines the core palette, spacing, and semantic tokens. This allows for easy implementation of dark/light modes and thematic updates.
2.  **Typography (`dpd-fonts.css`):** Encapsulates the complex font-face rules required for Pāḷi diacritics.
3.  **Master Styles (`dpd.css`):** The primary stylesheet for dictionary entries, focusing on readability and information hierarchy.
4.  **Legacy Support (`legacy.css`):** Preserves styles needed for older interfaces or specific backward-compatibility requirements.

## Relationships & Data Flow
- **Export Pipeline:** Every subsystem in **exporter/** (GoldenDict, WebApp, PDF) references these files during their build or runtime rendering phases.
- **Identity Root:** Complements the logos and fonts in the parent **identity/** directory.

## Interface
These are static assets. Developers update the project's look-and-feel by modifying the rules here. No execution is required.
