#!/usr/bin/env python3

"""Remove all sbs rows which not relevant for sbs study tools"""
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

from sqlalchemy.orm import joinedload


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    # Assuming DpdHeadword has a relationship to sbs that is a queryable entity
    db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).all()

    with db_session.no_autoflush:
        for i in db:
            if i.sbs:
                # Check for the absence of specified fields
                should_delete = not any([
                    i.sbs.sbs_class_anki,
                    i.sbs.sbs_patimokkha,
                    i.sbs.sbs_index,
                    i.sbs.sbs_category,
                ])

                if should_delete:
                    # Delete the related sbs entry
                    print(f"Deleting SBS entry for Word ID: {i.id}")
                    db_session.delete(i.sbs)

        # Commit after processing all records
        db_session.commit()
        print("Deletion of entries completed.")

if __name__ == "__main__":
    main()






