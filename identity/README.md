# identity/

## Purpose & Rationale
The `identity/` directory is the project's aesthetic and branding core. It exists to ensure that regardless of the platform (web, offline dictionary, PDF), the project presents a unified, professional, and readable visual experience. It solves the problem of fragmented styling and inconsistent display.

## Architectural Logic
This directory follows a "Shared Asset Library" pattern. It centralizes the CSS, fonts, and logos that define the DPD brand identity. By decoupling visual styling from the logic of the exporters, the project can update its entire look-and-feel from a single location.

## Relationships & Data Flow
- **Styling:** The master CSS files here are the source for all **Exporters**.
- **Branding:** Logos and icons are pulled into the **Docs** and **WebApp**.
- **Display:** Specialized fonts are provided here to ensure correct rendering of Pāḷi text across all supported devices.

## Interface
This folder contains static assets referenced by other systems. It is not intended to be executed.
