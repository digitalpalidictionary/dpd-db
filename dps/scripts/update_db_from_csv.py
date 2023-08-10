"""A tutoiral and template to update the database using a external csv. copy from https://github.com/digitalpalidictionary/dpd-db/blob/main/scripts/update_db_from_some_csv.py"""


from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths as PTH
from dps.tools.paths_dps import DPSPaths as DPSPTH
from tools.tsv_read_write import read_tsv_dot_dict


db_session = get_db_session(PTH.dpd_db_path)

# put in the path of the csv you want to open
csv_path = DPSPTH.temp_csv_path

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
for i in csv:

    # find the column name you want to change, in this case "sbs.sbs_class"
    if i.sbs_class:
        # this find the dpd word which matches the id
        # here you could also use Russian or SBS instead of PaliWord
        csv_id = i.id
        db_entry = db_session.query(PaliWord).filter(
            PaliWord.id == csv_id).first()

        # this updates the db entry with the csv value
        print(f"old: {db_entry.sbs.sbs_class}")
        db_entry.sbs.sbs_class = i.sbs_class
        print(f"new: {db_entry.sbs.sbs_class}")
        print()

# check that the output is as expected, then uncomment commit
db_session.commit()

# dont forget to always close the db session
db_session.close()
