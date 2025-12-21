# archive/

## Purpose & Rationale
`archive/` is the project's institutional memory. Its rationale is to preserve deprecated logic, legacy data formats, and experimental code that is no longer part of the production pipeline but remains valuable for historical reference or as a source of techniques for future migrations. It solves the problem of "losing" the reasoning behind past architectural decisions.

## Architectural Logic
This directory follows a "Preservation without Dependency" pattern. Contents are organized by their original subsystem (db, exporter, web_app_old) but are intentionally disconnected from the current project's build and test suites.

## Relationships & Data Flow
- **Historical Source:** Contains the "Old Web App" and early versions of the deconstructor and frequency engines.
- **Reference Only:** No data should flow *from* this directory into the current production systems.

## Interface
Read-only reference. These scripts are not intended to be executed in the current environment.