# db/

## Purpose & Rationale
The `db/` directory is the heart of the project's data lifecycle. Its primary purpose is to manage the complex transition from raw lexicographical data to a structured, relational database. It exists to solve the problem of data integrity, normalization, and the efficient generation of "derived data" (like inflections) that are too computationally expensive to calculate on-the-fly during dictionary use.

## Architectural Logic
This subsystem follows a "Build and Derive" pattern:
1.  **Modeling:** Data is structured via SQLAlchemy models to ensure type safety and relational integrity.
2.  **Population:** Core source tables (manually edited or imported) are used as the foundation.
3.  **Derivation:** Intensive processes (inflection generation, frequency mapping, lookup indexing) are run to pre-calculate the data that makes the dictionary performant.
4.  **Versioning:** TSV backups are maintained to track changes in the underlying source data independently of the binary `.db` file.

## Relationships & Data Flow
- **Input:** Raw data often enters via the **GUI** or imports from **Shared Data**.
- **Output:** The resulting populated database is the single source of truth for all **Exporters**.
- **Utility:** It relies on **Tools** for linguistic sorting and text cleaning during the derivation phase.

## Interface
Developers primarily interact with this subsystem via the SQLAlchemy models in `models.py` or by running the derivation/build scripts located in `scripts/build/`.