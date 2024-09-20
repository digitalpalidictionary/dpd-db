"""A tutoiral and template to update the database using a external TSV."""

from pathlib import Path
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

# put in the path of the csv you want to open
csv_path = Path("../csvs/dpd-full.csv")

# make a dot_dict of the csv
csv = read_tsv_dot_dict(csv_path)
print("[yellow]first entry in the csv")
print(csv[0])
input("press enter to continue: ")

# make a list of columns
columns = [key for key in csv[0].keys()]
print("[yellow]columns in the csv")
print(columns)
input("press enter to continue: ")


# iterate through the csv item by item
for i in csv:

    # find the column name you want to change, in this case "Category"
    if i.Category:
        # this find the dpd word which matches the user_id
        # here you could also use Russian or SBS instead of DpdHeadword
        csv_user_id = i.ID
        db_entry = db_session.query(DpdHeadword).filter(
            DpdHeadword.user_id == csv_user_id).first()

        # this updates the db entry with the csv value
        print(f"old: {db_entry.family_set}")
        db_entry.family_set = i.Category
        print(f"new: {db_entry.family_set}")
        print()

# check that the output is as expected, then uncomment commit
# db_session.commit()

# dont forget to always close the db session
db_session.close()
