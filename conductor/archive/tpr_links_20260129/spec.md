# Specification: Tipiṭaka Pāḷi Reader (TPR) Links

## Overview
Add deep links to the Tipiṭaka Pāḷi Reader (TPR) application in the Sutta tab of the DPD webapp. This allows users to jump directly from a sutta entry in DPD to the corresponding text in the TPR desktop/mobile app.

## Functional Requirements
1.  **TPR Sutta Code Extraction**: 
    - Extract a list of unique `sutta_shortcut` codes from the TPR SQLite database (`~/.local/share/tipitaka_pali_reader/tipitaka_pali.db`).
    - Save this list as a resource (e.g., JSON or Pickle) for efficient lookup.
2.  **Data Access Layer**:
    - Implement a loader in `tools/cache_load.py` to load the TPR sutta codes into a memory-cached set.
3.  **Database Model Enhancement**:
    - Add a `has_tpr` property to the `SuttaInfo` class in `db/models.py`.
    - This property should return `True` if the current `cst_code` exists in the TPR sutta codes set.
4.  **UI Updates (`dpd_headword.html`)**:
    - Rename the "Websites using CST" heading to "Websites and apps using CST".
    - Add a row for "Tipiṭaka Pāḷi Reader" if `has_tpr` is true.
    - The link format MUST be: `tpr.pali.tools://open/?sutta={{ d.su.dpd_code.lower() }}`.
5.  **GoldenDict Integration**:
    - Update the relevant GoldenDict Jinja2 template (e.g., the one handling sutta information) to match the webapp changes.
    - Ensure the heading is renamed to "Websites and apps using CST" and the TPR link row is added.
    - The link should use the `tpr.pali.tools://` protocol.

## Non-Functional Requirements
- **Performance**: Use a set for $O(1)$ lookups during template rendering.
- **Simplicity**: No icons or complex tooltips; standard text link.

## Acceptance Criteria
- [ ] A list of TPR codes is generated and stored in the project.
- [ ] `SuttaInfo.has_tpr` correctly identifies suttas available in TPR based on `cst_code`.
- [ ] The Sutta tab heading is updated.
- [ ] TPR links appear only for suttas that exist in the TPR database.
- [ ] Clicking the link (on a device with TPR installed) attempts to open the TPR app.

## Out of Scope
- Automatic installation or detection of the TPR app.
- Links to commentary or sub-commentary (Vansas) unless they are part of the primary `sutta_shortcut` list.
