# db/backup_tsv/

## Purpose & Rationale
The `backup_tsv/` directory is the project's data versioning layer. It exists to solve the fundamental problem of tracking changes in a relational database using Git. Since binary `.db` files are opaque to version control, this directory stores "exploded" text-based representations (TSV) of the primary source tables. It bridges the gap between the live SQLite database and the Git version control system, ensuring that every change made to a headword or root is captured in a transparent, text-based format that can be tracked, audited, and recovered.

## Architectural Logic
This subsystem follows a "Synchronized Serialization" and "Data Serialized for Git" pattern:
1.  **Dumping & Serialization:** `backup_dpd_headwords_and_roots.py` extracts the full state of the primary `DpdHeadword` and `DpdRoot` tables from the SQLite database.
2.  **Chunking:** It automatically splits large tables (like `dpd_headwords`) into multiple TSV parts to keep file sizes manageable, ensuring that Git diffs remain readable and that individual file size limits are respected.
3.  **Atomicity:** Each row in the TSV corresponds to a record in the database, allowing for line-by-line tracking of additions, deletions, and modifications to specific Pāḷi words or roots.
4.  **Git Integration:** The logic handles the automatic staging and committing of these TSV changes, ensuring the backup process is tightly coupled with the project's source control.
5.  **Recovery:** These files act as the ultimate backup, from which the SQLite database can be fully reconstructed.

## Relationships & Data Flow
- **Source:** Pulls from the live `dpd.db` SQLite database using **db/** models.
- **Outward Bound:** Data flows from the SQLite database to these TSVs via the `backup_dpd_headwords_and_roots.py` script now located in this directory.
- **Inward Flow:** These resulting TSVs are the primary input for the `scripts/build/` process, completing the data lifecycle loop. During a fresh build or after a major data merge, these TSVs are used to populate the tables defined in `db/models.py`.

## Interface
Developers primarily interact with this directory via:
- **Trigger Backup:** `uv run python db/backup_tsv/backup_dpd_headwords_and_roots.py`
(Run this script whenever significant manual data capture or batch corrections have been performed).
- **Populate DB:** `uv run python scripts/build/build_db.py` (To populate the DB from these TSVs)