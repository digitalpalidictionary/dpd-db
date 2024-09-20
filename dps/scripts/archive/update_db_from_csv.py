"""A tutoiral and template to update the database using a external csv. copy from https://github.com/digitalpalidictionary/dpd-db/blob/main/scripts/update_db_from_some_csv.py"""


from rich.console import Console

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from tools.tsv_read_write import read_tsv_dot_dict

console = Console()
pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)

# put in the path of the csv you want to open
csv_path = dpspth.temp_csv_path

print(f"[yellow]updating db from {csv_path}")


# make a dot_dict of the csv
csv = read_tsv_dot_dict(csv_path)
print(f"[blue]first entry after headings in the csv: {csv[1]} ")
input("press enter to continue: ")

# make a list of columns
columns = [key for key in csv[0].keys()]
print(f"[blue]{columns} columns in the csv")
input("press enter to continue: ")


# iterate through the csv item by item
for idx, i in enumerate(csv, start=1):  # start=1 will start the indexing from 1

    # find the column name you want to change, in this case "sbs.sbs_class"
    if i.sbs_class:
        # this find the dpd word which matches the id
        csv_id = i.id
        db_entry = db_session.query(DpdHeadword).filter(
            DpdHeadword.id == csv_id).first()

        if db_entry and db_entry.sbs:
            # this updates the db entry with the csv value
            print(f"Row number: {idx}")
            print(f"old: {db_entry.sbs.sbs_class}")
            db_entry.sbs.sbs_class = i.sbs_class
            print(f"new: {db_entry.sbs.sbs_class}")
            print()


# check that the output is as expected, then uncomment commit
# db_session.commit()

# dont forget to always close the db session
db_session.close()
