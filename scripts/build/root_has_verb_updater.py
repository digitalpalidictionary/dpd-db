#!/usr/bin/env python3

"""Update DpdRoot.root_has_verb column based on the current DpdHeadword data."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class RootHasVerbUpdater:
    def __init__(self):
        pr.tic()
        pr.title("testing which roots have verbs")

        self.verbs: list[str] = [
            "pr",
            "aor",
            "perf",
            "imperf",
            "inf",
            "abs",
            "prp",
            "pp",
            "ptp",
        ]
        self.verb_yes: str = "･"
        self.verb_no: str = "×"

        self.prepare_database()
        self.make_root_has_verb_dict()
        self.update_root_has_verb()
        self.update_db()

        pr.toc()

    def prepare_database(self):
        pr.green("preparing data")
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.dpd_db: list[DpdHeadword] = (
            self.db_session.query(DpdHeadword)
            .filter(DpdHeadword.root_key != "")
            .order_by(DpdHeadword.root_key)
            .all()
        )
        self.roots_db: list[DpdRoot] = self.db_session.query(DpdRoot).all()
        pr.yes(len(self.dpd_db))

    def test_root_has_verb(self) -> bool:
        if (
            self.i.pos in self.verbs
            and "deno" not in self.i.grammar
            and "deno" not in self.i.verb
        ):
            return True
        else:
            return False

    def make_root_has_verb_dict(self) -> None:
        pr.green("testing roots have verbs")
        self.root_has_verb_dict: dict[str, str] = {}
        current_root = ""
        has_verb: bool
        for self.i in self.dpd_db:
            if self.i.root_key != current_root:
                current_root = self.i.root_key
                has_verb = False
                self.root_has_verb_dict[self.i.root_key] = self.verb_no

            if has_verb is False:
                test_result = self.test_root_has_verb()
                if test_result:
                    has_verb = True
                    self.root_has_verb_dict[self.i.root_key] = self.verb_yes

        pr.yes(len(self.root_has_verb_dict))

    def update_root_has_verb(self) -> None:
        self.updated = 0
        for i in self.roots_db:
            root_has_verb_nu = self.root_has_verb_dict[i.root]
            if root_has_verb_nu == i.root_has_verb:
                pass
            else:
                pr.red(f"{i.root} {root_has_verb_nu}")
                i.root_has_verb = root_has_verb_nu
                self.updated += 1

    def update_db(self):
        pr.green("updating db")
        if self.updated:
            self.db_session.commit()
        pr.yes(self.updated)


def main():
    RootHasVerbUpdater()


if __name__ == "__main__":
    main()
