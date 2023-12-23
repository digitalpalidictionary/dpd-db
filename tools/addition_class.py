"""A class to handle all data relevant to adding user additions to the db."""

import pickle

from datetime import datetime
from rich import print
from typing import Optional

from db.models import PaliWord
from tools.paths import ProjectPaths

pth = ProjectPaths()

class Addition:
    def __init__(
            self,
            pali_word: PaliWord,
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

    def __repr__(self):
        return f"""
{'pali_word':<20}{self.pali_word}
{'comment':<20}{self.comment}
{'date_created':<20}{self.date_created}
{'old_id':<20}{self.old_id}
{'new_id':<20}{self.new_id}
{'added_to_db':<20}{self.added_to_db}
{'added_date':<20}{self.added_date}
"""

if __name__ == "__main__":
    additions_list = Addition.load_additions()
    [print(a) for a in additions_list]
        

