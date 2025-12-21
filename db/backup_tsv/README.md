# db/backup_tsv/

## Purpose & Rationale
The `backup_tsv/` directory is the project's data versioning layer. It exists to solve the fundamental problem of tracking changes in a relational database using Git. Since binary `.db` files are opaque to version control, this directory stores "exploded" text-based representations (TSV) of the primary source tables.

## Architectural Logic
This directory follows a "Data Serialized for Git" pattern:
1.  **Serialization:** Large tables (like `dpd_headwords`) are exported into multiple TSV parts to keep file sizes manageable and diffs readable.
2.  **Atomicity:** Each row in the TSV corresponds to a record in the database, allowing for line-by-line tracking of additions, deletions, and modifications to specific Pāḷi words or roots.
3.  **Recovery:** These files act as the ultimate backup, from which the SQLite database can be fully reconstructed.

## Relationships & Data Flow
- **Outward Bound:** Data flows from the SQLite database to these TSVs via backup scripts in `scripts/backup/`.
- **Inward Bound:** During a fresh build or after a major data merge, these TSVs are used to populate the tables defined in `db/models.py`.

## Interface
Developers rarely edit these files manually. They are primarily interacted with via:
- `uv run python scripts/backup/backup_db.py` (To update the TSVs from the DB)
- `uv run python scripts/build/build_db.py` (To populate the DB from these TSVs)
