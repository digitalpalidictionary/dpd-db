"""A class to handle all data relevant to adding user additions to the db."""

import pickle
import pandas as pd

from datetime import datetime
from rich import print
from typing import Optional

from db.models import DpdHeadwords
from db.db_helpers import get_db_session, get_column_names
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict, write_tsv_dot_dict
from tools.tsv_read_write import read_tsv_as_dict, write_tsv_dot_dict


pth = ProjectPaths()

# When secondary user adds new words gets added to their db > save it to the Additions TSV
# When secondary user updates a word in their db > update the Additions TVS
# When primary user adds the Additions to their database, save the new id and comments 
# TODO Process to add new Additions one by one.


class Additions():

    def __init__(
        self,
        headword: DpdHeadwords,
        comment: str
    ):
        self.additions_list: list[dict] = self.load_additions_tsv()
        self.add_me = {
            "new_id": "",
            "comment": comment,
            "date_created": str(datetime.now().strftime('%Y-%m-%d')),
            "added_to_db": "",
            "date_added_to_db": "",
        }
        self.add_me.update(headword.__dict__)
        self.add_me.pop("_sa_instance_state")
        self.add_me.pop("updated_at")
        self.add_me.pop("created_at")
        
        self.id_exists: bool = False
        self.pop_id_if_exists()
        self.additions_list.append(self.add_me)
        self.save_additions_tsv()

    def load_additions_tsv(self):
        try:
            return read_tsv_dot_dict(pth.additions_tsv_path)
        except FileNotFoundError:
            return []

    def save_additions_tsv(self):
        write_tsv_dot_dict(pth.additions_tsv_path, self.additions_list)
    
    def pop_id_if_exists(self):
        """Test if the id already exist and pop it if it does."""

        add_me_id = self.add_me["id"]
        for counter, i in enumerate(self.additions_list):
            if str(i.id) == str(add_me_id):
                self.additions_list.pop(counter)
                break
    

    def convert_old_format_to_new():
        with open(pth.additions_pickle_path, "rb") as f:
            old_additions_list = pickle.load(f)
            for i in old_additions_list:
                print(i)



if __name__ == "__main__":

    db_session = get_db_session(pth.dpd_db_path)
    headword = db_session.query(DpdHeadwords).filter_by(id=83).first()
    # Additions(headword, "sure?!")
    Additions.convert_old_format_to_new()
