"""Update Russian table from an external csv."""

from rich.console import Console

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from tools.tsv_read_write import read_tsv_dot_dict

from sqlalchemy.orm import joinedload


console = Console()
pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)

# put in the path of the csv you want to open
csv_path = dpspth.ru_apply_path

console.print(f"[yellow]Updating db from {csv_path}")

# make a dot_dict of the csv
csv = read_tsv_dot_dict(csv_path)
console.print(f"[blue]First entry after headings in the csv: {csv[1]}")
console.print(f"[blue]Total number of rows in the file: {len(csv)}")
input("Press enter to continue: ")

count_meanings = 0
count_lit = 0

# iterate through the csv item by item
for idx, i in enumerate(csv, start=1):
    csv_id = i.id
    db_entry = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.ru)).filter(DpdHeadword.id == csv_id).first()

    if db_entry and db_entry.ru:

        # Update ru_meaning
        if i.corrections_ru_meaning:
            db_entry.ru.ru_meaning = i.corrections_ru_meaning
            count_meanings += 1
            console.print(f"[green]Processing Row number: {idx} {i.id}")
            console.print(f"Updated ru_meaning with corrections: {i.corrections_ru_meaning}")
        
        elif i.ru_meaning and not db_entry.ru.ru_meaning:
            db_entry.ru.ru_meaning = i.ru_meaning
            count_meanings += 1
            console.print(f"[green]Processing Row number: {idx} {i.id}")
            console.print(f"Updated empty ru_meaning with: {i.ru_meaning}")
            

        # Update ru_meaning_lit
        if i.corrections_ru_meaning_lit:
            db_entry.ru.ru_meaning_lit = i.corrections_ru_meaning_lit
            count_lit += 1
            console.print(f"[green]Processing Row number: {idx} {i.id}")
            console.print(f"Updated ru_meaning_lit with corrections: {i.corrections_ru_meaning_lit}")
            
        elif i.ru_meaning_lit and not db_entry.ru.ru_meaning_lit:
            db_entry.ru.ru_meaning_lit = i.ru_meaning_lit
            count_lit += 1
            console.print(f"[green]Processing Row number: {idx} {i.id}")
            console.print(f"Updated empty ru_meaning_lit with: {i.ru_meaning_lit}")
            

        console.print()

# check that the output is as expected, then uncomment commit
# db_session.commit()

# don't forget to always close the db session
db_session.close()

console.print("[green]Database update process completed.")
console.print(f"Number of updated ru_meanings: {count_meanings}")
console.print(f"Number of updated ru_meaning_lit: {count_lit}")