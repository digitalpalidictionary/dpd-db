from sqlalchemy import create_engine, case
from sqlalchemy.orm import sessionmaker
from audio.db.models import DpdAudio
from tools.paths import ProjectPaths
import os
import sys

# Setup
pth = ProjectPaths()
db_path = pth.dpd_audio_db_path

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    sys.exit(1)

engine = create_engine(f"sqlite+pysqlite:///{db_path}", echo=True)  # Echo to see SQL
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

print("Querying with optimizations...")
# Optimization: check for existence without loading the blob
# We use a limit to avoid printing too much, but in reality we'd do .all()
try:
    results = (
        session.query(
            DpdAudio.lemma_clean,
            case((DpdAudio.male1 != None, True), else_=False).label("has_male1"),
            case((DpdAudio.male2 != None, True), else_=False).label("has_male2"),
            case((DpdAudio.female1 != None, True), else_=False).label("has_female1"),
        )
        .limit(5)
        .all()
    )

    for r in results:
        print(f"Lemma: {r[0]}, Male1: {r[1]}, Male2: {r[2]}, Female1: {r[3]}")

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
