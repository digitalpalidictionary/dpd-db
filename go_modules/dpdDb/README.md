# go_modules/dpdDb/

## Purpose & Rationale
`dpdDb/` is the project's high-performance database access layer. Its rationale is to provide a Go-native interface to the `dpd.db` SQLite file, enabling other Go modules (like the deconstructor and frequency engine) to query and update the database with maximum speed and minimum memory overhead.

## Architectural Logic
This subsystem follows a "Thin ORM Wrapper" pattern:
1.  **Modeling (`model.go`):** Re-implements the project's core data models (Headwords, Roots, etc.) in Go structs, carefully aligned with the SQLAlchemy models in **db/models.py**.
2.  **Access (`db.go`):** Provides standardized connection and query logic using the GORM library.
3.  **Cross-Compatibility:** Its primary goal is to ensure that Go-based logic interacts with the *same* database schema as the Python-based logic, maintaining data integrity across the entire heterogeneous codebase.

## Relationships & Data Flow
- **Bridge:** Connects the **go_modules/** ecosystem to the project's primary SQLite database.
- **Consistency:** Must be manually synchronized if the Python SQLAlchemy models change.

## Interface
This is a supporting package intended to be imported by other Go modules within the project.
