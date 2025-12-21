# identity/logo/

## Purpose & Rationale
`identity/logo/` is the project's visual hallmark. Its rationale is to provide high-quality, multi-format versions of the DPD brand assets. It ensures that the project is instantly recognizable across its diverse touchpoints, from browser favicon to Kindle cover.

## Architectural Logic
Assets are provided in a hierarchy of formats:
1.  **SVG (Master):** Resolution-independent source files for maximum quality at any size.
2.  **PNG (Raster):** Web-optimized versions for the WebApp and general documentation.
3.  **BMP (Legacy/Specialized):** Specific formats required by older dictionary engines or specialized device exporters.
4.  **Icons:** Small-scale variants optimized for UI elements and browser tabs.

## Relationships & Data Flow
- **Consumption:** Pulled into **docs/**, **exporter/webapp/**, and **exporter/kindle/**.
- **Reference:** Acts as the official source for anyone wishing to link to or cite the project.

## Interface
Static image assets. No execution required.
