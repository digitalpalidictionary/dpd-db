#!/usr/bin/env python3

"""Move all examples to lower position if the position is empty"""
from rich import print
import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SBS
from tools.paths import ProjectPaths

from sqlalchemy.orm import joinedload

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).outerjoin(SBS).all()


def dhp():
    for i in db:
        # if i.sbs:

        #     # Check for "DHP" followed by a digit in sbs_source fields
        #     for idx in range(1, 5):  # Assuming there are 4 positions
        #         sbs_source_value = getattr(i.sbs, f"sbs_source_{idx}")
        #         if sbs_source_value and re.search(r"DHP\d", sbs_source_value):
        #             # Copy values to dhp fields
        #             for field_prefix in ['source', 'sutta', 'example']:
        #                 sbs_value = getattr(i.sbs, f"sbs_{field_prefix}_{idx}")
        #                 setattr(i.sbs, f"dhp_{field_prefix}", sbs_value)
        #                 print(f"{i.id} {sbs_value}")
        # ! not working!  only if meaning_1
        if not i.sbs:

            # Fetch the existing SBS object from the database
            existing_sbs = db_session.query(SBS).get(i.id)

            # Check for "DHP" followed by a digit in source fields
            for idx in range(1, 3):  # Assuming there are 2 positions
                source_value = getattr(i, f"source_{idx}")
                if source_value and re.search(r"DHP\d", source_value) and i.meaning_1:
                    # Copy values to dhp fields
                    if existing_sbs:
                        print(f"{i.id}")
                        # db_session.commit()
                        for field_prefix in ['source', 'sutta', 'example']:
                            value = getattr(i, f"{field_prefix}_{idx}")
                            setattr(existing_sbs, f"dhp_{field_prefix}", value)
                            print(f"{i.id} {value}")
                    else:
                        existing_sbs = SBS(id=i.id)

    # Commit after processing all records
    # db_session.commit()
    db_session.close()
    print("All changes committed.")


def pali_class():
    with db_session.no_autoflush:
        for i in db:
            if i.sbs:
                if i.sbs.sbs_class_anki:
                    if i.sbs.sbs_example_1 and not i.sbs.sbs_example_2:
                        # move from example_1 to class_example
                        i.sbs.class_example = i.sbs.sbs_example_1
                        i.sbs.class_source = i.sbs.sbs_source_1
                        i.sbs.class_sutta = i.sbs.sbs_sutta_1

                        print(f"{i.id} {i.sbs.class_source}")


        # Commit after processing all records
        # db_session.commit()
        print("All changes committed.")


def pat():
    with db_session.no_autoflush:
        for i in db:
            if i.sbs:
                if i.sbs.sbs_patimokkha:
                    # Check for "VIN PAT" in sbs_source fields
                    for idx in range(1, 5):  # Assuming there are 4 positions
                        sbs_source_value = getattr(i.sbs, f"sbs_source_{idx}")
                        if sbs_source_value and re.search(r"VIN PAT", sbs_source_value):
                            # Copy values to pat fields
                            for field_prefix in ['source', 'sutta', 'example']:
                                sbs_value = getattr(i.sbs, f"sbs_{field_prefix}_{idx}")
                                setattr(i.sbs, f"pat_{field_prefix}", sbs_value)
                                print(f"{i.id} {sbs_value}")
            #  ! not working!
            if not i.sbs:
                print("add examples from source_1 and 2 only if meaning_1")


        # Commit after processing all records
        # db_session.commit()
        print("All changes committed.")


def discor():
    with db_session.no_autoflush:
        for i in db:
            if i.sbs:
                #  ! also move examples which from different source ex mn107 has SN56.11 examples etc.
                if i.sbs.sbs_category == "sn12":
                    # Check for "Sutta" in sbs_source fields
                    for idx in range(1, 5):  # Assuming there are 4 positions
                        sbs_source_value = getattr(i.sbs, f"sbs_source_{idx}")
                        if sbs_source_value and re.search(r"SN12", sbs_source_value):
                            # Copy values to pat fields
                            for field_prefix in ['source', 'sutta', 'example']:
                                sbs_value = getattr(i.sbs, f"sbs_{field_prefix}_{idx}")
                                setattr(i.sbs, f"discourses_{field_prefix}", sbs_value)
                                print(f"{i.id} {sbs_value}")
            #  ! not working!
            if not i.sbs:
                # maybe search examples from source_1 and 2
                for idx in range(1, 3):
                    source_value = getattr(i, f"source_{idx}")
                    if source_value and re.search("SN56.69", source_value) and i.meaning_1:
                        # Copy values to dhp fields
                        print(f"{i.id}")
                        # db_session.commit()
                        for field_prefix in ['source', 'sutta', 'example']:
                            value = getattr(i, f"{field_prefix}_{idx}")
                            # setattr(existing_sbs, f"dhp_{field_prefix}", value)
                            print(f"in dpd {i.id} {value}")




        # Commit after processing all records
        db_session.commit()
        print("All changes committed.")


if __name__ == "__main__":
    # dhp()
    # pali_class()
    # pat()
    discor()