from rich import print
from sqlalchemy import inspect
import csv

from db.get_db_session import get_db_session
from db.models import PaliWord, PaliRoot

print("[bright_yellow]backing up db to tsv")
print("[green]getting db session")
db_session = get_db_session("dpd.db")

print("[green]querying PaliWord")
db = db_session.query(PaliWord).all()

print("[green]writing PaliWord rows")
with open("backups/PaliWord.tsv", 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter="\t")
    csvwriter.writerow([column.name for column in PaliWord.__mapper__.columns])
    [csvwriter.writerow([getattr(curr, column.name)
                             for column in PaliWord.__mapper__.columns]) for curr in db]

print("[green]querying PaliRoot")
db = db_session.query(PaliRoot).all()

print("[green]writing PaliRoot rows")
with open("backups/PaliRoot.tsv", 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter="\t")
    csvwriter.writerow([column.name for column in PaliRoot.__mapper__.columns])
    [csvwriter.writerow([getattr(curr, column.name)
                         for column in PaliRoot.__mapper__.columns]) for curr in db]


