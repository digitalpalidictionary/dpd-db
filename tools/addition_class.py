"""A class to handle all data relevant to adding user additions to the db."""

from datetime import datetime

from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict, write_tsv_dot_dict
from tools.configger import config_read

pth = ProjectPaths()

# When secondary user adds new words to their db > save it to the Additions TSV
# When secondary user updates a word in their db > update the Additions TVS
# When primary user adds the Additions to their database, save the new id and comments
# TODO Process to add new Additions one by one.


class Additions:
    def __init__(
        self,
        headword: DpdHeadword,
    ):
        self.headword: DpdHeadword = headword
        self.additions_list: list[dict] = self.load_additions_tsv()
        self.add_me = {
            "new_id": "",
            "comment": "",
            "date_created": str(datetime.now().strftime("%Y-%m-%d")),
            "added_to_db": "",
            "date_added_to_db": "",
            "name": config_read("user", "username"),
        }
        self.add_me.update(headword.__dict__)
        self.add_me.pop("_sa_instance_state")
        try:
            self.add_me.pop("updated_at")
            self.add_me.pop("created_at")
        except KeyError:
            pass
        self.is_new_addition = self.test_id()
        if self.add_me["added_to_db"]:
            self.needs_updating = False
        else:
            if self.is_new_addition:
                self.needs_updating = False
            else:
                self.needs_updating = True

    def load_additions_tsv(self):
        try:
            return read_tsv_dot_dict(pth.additions_tsv_path)
        except FileNotFoundError:
            return []

    def save_additions_tsv(self):
        write_tsv_dot_dict(pth.additions_tsv_path, self.additions_list)

    def test_id(self):
        self.id_index: int | None = None
        for counter, add_list in enumerate(self.additions_list):
            if str(add_list["id"]) == str(self.add_me["id"]):
                # pop and add if it exists
                self.additions_list.pop(counter)
                return False

        return True

    def update(self, comment: str):
        self.add_me["comment"] = comment
        self.additions_list.append(self.add_me)
        self.save_additions_tsv()

    def __repr__(self) -> str:
        return f"""
{"id":<20}: {self.add_me["id"]}
{"lemma_1":<20}: {self.add_me["lemma_1"]}
{"comment":<20}: {self.add_me["comment"]}
{"new_id":<20}: {self.add_me["new_id"]}
{"date_created":<20}: {self.add_me["date_created"]}
{"added_to_db":<20}: {self.add_me["added_to_db"]}
{"date_added_to_db":<20}: {self.add_me["date_added_to_db"]}
"""


if __name__ == "__main__":
    # db_session = get_db_session(pth.dpd_db_path)
    # headword = db_session.query(DpdHeadword).filter_by(id=45673).first()
    # if headword:
    #     new_addition = Additions(headword)
    #     print(new_addition.needs_updating)
    #     new_addition.update("oh yes!")
    # add_to_db()
    pass
