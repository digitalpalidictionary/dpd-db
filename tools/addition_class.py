"""A class to handle all data relevant to adding user additions to the db."""

import pickle
import pandas as pd

from datetime import datetime
from rich import print
from sqlalchemy.orm.session import make_transient
from typing import Optional

from db.models import DpdHeadwords, PaliWord
from tools.paths import ProjectPaths

pth = ProjectPaths()

class Addition:
    def __init__(
            self,
            pali_word: DpdHeadwords,
            comment: str,
            date_created: Optional[str] = None,
            old_id: Optional[int] = None,
            new_id: Optional[int] = None,
            added_to_db: bool = False,
            added_date: Optional[str] = None
    ):
        self.pali_word = pali_word
        self.comment = comment
        if date_created is None:
            self.date_created = datetime.now().strftime('%Y-%m-%d')
        else:
            self.date_created = date_created
        self.old_id = pali_word.id
        self.new_id = new_id
        self.added_to_db = added_to_db
        self.added_date = added_date

    def update(
            self,
            new_id: int,
            added_to_db: bool = True,
            added_date: Optional[str] = None):
        self.new_id = new_id
        self.added_to_db = added_to_db
        if added_date is None:
            self.added_date = datetime.now().strftime('%Y-%m-%d')
        else:
            self.added_date = added_date

    @ staticmethod
    def load_additions():
        with open(pth.additions_pickle_path, "rb") as file:
            additions_list = pickle.load(file)
        return additions_list

    @ staticmethod
    def save_additions(additions_list):
        with open(pth.additions_pickle_path, "wb") as file:
            pickle.dump(additions_list, file)


    def replace_id_in_file(self, file_path, checking_data):
        try:
            df = pd.read_csv(file_path, sep='\t', header=None, low_memory=False, on_bad_lines='skip')
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return

        if (
            self.new_id is not None and
            self.added_date is not None and
            datetime.strptime(self.added_date, '%Y-%m-%d') >= datetime.strptime(checking_data, '%Y-%m-%d')
        ):
            df[0] = df[0].apply(lambda x: (print(f"Old ID: {x}, New ID: {self.new_id} in {file_path}") or str(self.new_id)) if str(x) == str(self.old_id) else x)
            df.to_csv(file_path, sep='\t', index=False, header=False)


    def __repr__(self):
        return f"""
{'comment':<20}{self.comment}
{'date_created':<20}{self.date_created}
{'pali_word':<20}{self.pali_word}
{'old_id':<20}{self.old_id}
{'new_id':<20}{self.new_id}
{'added_to_db':<20}{self.added_to_db}
{'added_date':<20}{self.added_date}
"""

if __name__ == "__main__":
    additions_list = Addition.load_additions()
    print([a for a in additions_list])

    # from this added_date onward we going to replace old_id with new_id
    checking_data = "2024-02-14"

    # for addition in additions_list:
    #     addition.replace_id_in_file(pth.corrections_tsv_path, checking_data)
    #     addition.replace_id_in_file(pth.sbs_path, checking_data)
    #     addition.replace_id_in_file(pth.russian_path, checking_data)


