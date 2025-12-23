import sqlite3
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Assumes this script is run from within the dpd-db environment
from db.models import DpdHeadword, Lookup
from tools.paths import ProjectPaths


def create_mobile_db():
    pth = ProjectPaths()
    source_db = pth.dpd_db_path
    target_db = "../dpd-app/src/assets/dpd_mobile.db"

    os.makedirs(os.path.dirname(target_db), exist_ok=True)

    if os.path.exists(target_db):
        os.remove(target_db)

    print(f"Connecting to source: {source_db}...")
    engine = create_engine(f"sqlite:///{source_db}")
    Session = sessionmaker(bind=engine)
    session = Session()

    # Introspect the DpdHeadword model to get ALL actual column names and types
    mapper = inspect(DpdHeadword)
    column_names = [c.key for c in mapper.column_attrs]

    print(f"Identified {len(column_names)} columns in DpdHeadword model.")

    print(f"Creating target: {target_db}...")
    target_conn = sqlite3.connect(target_db)
    target_cursor = target_conn.cursor()

    # 1. Create dpd_headwords table with ALL columns
    # Programmatically determine types (mapping SQLAlchemy types to SQLite types)
    sql_cols = []
    for attr in mapper.column_attrs:
        col = attr.columns[0]
        col_type = "TEXT"
        if str(col.type).startswith("INTEGER"):
            col_type = "INTEGER"
        elif str(col.type).startswith("DATETIME"):
            col_type = "TEXT"

        pk = " PRIMARY KEY" if col.primary_key else ""
        sql_cols.append(f"{col.name} {col_type}{pk}")

    create_headwords_sql = f"CREATE TABLE dpd_headwords ({', '.join(sql_cols)})"
    target_cursor.execute(create_headwords_sql)

    # 2. Create lookup table
    target_cursor.execute(
        "CREATE TABLE lookup (lookup_key TEXT PRIMARY KEY, headwords TEXT)"
    )

    # 3. Copy Data for dpd_headwords
    print("Copying all dpd_headwords data...")
    all_words = session.query(DpdHeadword).all()

    headwords_data = []
    for w in all_words:
        row_data = []
        for attr in mapper.column_attrs:
            val = getattr(w, attr.key)
            # Handle non-serializable types if necessary
            if val is not None and attr.key in ["created_at", "updated_at"]:
                val = str(val)
            row_data.append(val)
        headwords_data.append(tuple(row_data))

    placeholders = ",".join(["?"] * len(column_names))
    target_cursor.executemany(
        f"INSERT INTO dpd_headwords VALUES ({placeholders})", headwords_data
    )

    # 4. Copy Data for lookup
    print("Copying lookup data...")
    lookup_results = session.query(Lookup).all()
    lookup_data = [
        (lu.lookup_key, lu.headwords) for lu in lookup_results if lu.headwords
    ]
    target_cursor.executemany("INSERT INTO lookup VALUES (?,?)", lookup_data)

    # 5. Create Indexes
    print("Creating indexes...")
    target_cursor.execute("CREATE INDEX idx_lemma ON dpd_headwords(lemma_1)")
    target_cursor.execute("CREATE INDEX idx_lookup_key ON lookup(lookup_key)")

    target_conn.commit()
    target_conn.close()
    session.close()

    size = os.path.getsize(target_db) / (1024 * 1024)
    print(
        f"Mobile DB created successfully. Included all {len(column_names)} columns. Size: {size:.2f} MB"
    )


if __name__ == "__main__":
    create_mobile_db()
