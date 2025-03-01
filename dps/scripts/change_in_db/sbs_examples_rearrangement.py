#!/usr/bin/env python3

"""Distribute sbs examples according to Anki deck"""
from rich import print
import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SBS, Russian
from tools.paths import ProjectPaths

from sqlalchemy.orm import joinedload

from dps.tools.sbs_table_functions import list_of_discourses

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
db = db_session.query(DpdHeadword) \
    .options(joinedload(DpdHeadword.sbs), joinedload(DpdHeadword.ru)) \
    .outerjoin(Russian, DpdHeadword.id == Russian.id) \
    .outerjoin(SBS, DpdHeadword.id == SBS.id) \
        .all()


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
                if i.sbs.sbs_patimokkha and not i.sbs.pat_source:
                    # Check for "VIN PAT" in sbs_source fields
                    for idx in range(1, 5):  # Assuming there are 4 positions
                        sbs_source_value = getattr(i.sbs, f"sbs_source_{idx}")
                        if sbs_source_value and re.search(r"VIN PAT", sbs_source_value):
                            # Copy values to pat fields
                            for field_prefix in ['source', 'sutta', 'example']:
                                sbs_value = getattr(i.sbs, f"sbs_{field_prefix}_{idx}")
                                # setattr(i.sbs, f"pat_{field_prefix}", sbs_value)
                                # print(f"{i.id} {sbs_value}")
                    for idx in range(1, 3):
                        source_value = getattr(i, f"source_{idx}")
                        if source_value and re.search(r"VIN PAT", source_value) and not re.search(r"VIN PAT PK", source_value) and i.meaning_1:
                            # Copy values to discourses fields
                            for field_prefix in ['source', 'sutta', 'example']:
                                value = getattr(i, f"{field_prefix}_{idx}")
                                setattr(i.sbs, f"pat_{field_prefix}", value)
                                print(f"{i.id} {value}")
                            break

                    
                # else:
                #     for idx in range(1, 3):
                #         source_value = getattr(i, f"source_{idx}")
                #         if source_value and re.search(r"VIN PAT", source_value) and not re.search(r"VIN PAT PK", source_value) and i.meaning_1:
                #             # Copy values to discourses fields
                #             for field_prefix in ['source', 'sutta', 'example']:
                #                 value = getattr(i, f"{field_prefix}_{idx}")
                #                 setattr(i.sbs, f"pat_{field_prefix}", value)

                #             # Change sbs_patimokkha to the lower letter version of the source
                #             # Extract the part before the first full stop or use the whole if no full stop
                #             category = source_value.split('.')[0].lower() + "_"
                #             i.sbs.sbs_patimokkha = category

                #             # print(f"Updated category for {i.id} to {category}")
                #             if not i.ru:
                #                 print(f"no ru {i.id}")
                            
                #             break

            # else:
            #     for idx in range(1, 3):
            #         source_value = getattr(i, f"source_{idx}")
            #         if source_value and re.search(r"VIN PAT", source_value) and not re.search(r"VIN PAT PK", source_value) and i.meaning_1:
            #             # Create a new SBS object with the same id as the DpdHeadword
            #             new_sbs = SBS(id=i.id)
            #             db_session.add(new_sbs)
            #             # Copy values to pat fields
            #             for field_prefix in ['source', 'sutta', 'example']:
            #                 value = getattr(i, f"{field_prefix}_{idx}")
            #                 setattr(new_sbs, f"pat_{field_prefix}", value)

            #             # Change sbs_patimokkha to the lower letter version of the source
            #             # Extract the part before the first full stop or use the whole if no full stop
            #             new_sbs.sbs_patimokkha = "pat_"

            #             print(f"Added category for {i.id} to 'pat_'")
            #             if not i.ru:
            #                 print(f"no ru {i.id}")
                        
            #             # db_session.commit()
            #             break  # Stop checking other discourses if one is found

        # Commit after processing all records
        # db_session.commit()
        print("All changes committed.")


def vib():
    with db_session.no_autoflush:
        for i in db:
            if i.sbs:
                if i.sbs.sbs_patimokkha == "vib":
                    # Check for "VIN1." in sbs_source fields
                    for idx in range(1, 5):  # Assuming there are 4 positions
                        sbs_source_value = getattr(i.sbs, f"sbs_source_{idx}")
                        if sbs_source_value and re.search(r"VIN1", sbs_source_value):
                            # Copy values to pat fields
                            for field_prefix in ['source', 'sutta', 'example']:
                                sbs_value = getattr(i.sbs, f"sbs_{field_prefix}_{idx}")
                                setattr(i.sbs, f"vib_{field_prefix}", sbs_value)
                                print(f"{i.id} {sbs_value}")

        # Commit after processing all records
        # db_session.commit()
        print("All changes committed.")


def discor():
    count = 0
    with db_session.no_autoflush:
        for i in db:
            # if i.sbs:
            #     # Iterate over each sbs_source field
            #     for idx in range(1, 5):  # Assuming there are 4 positions
            #         sbs_source_value = getattr(i.sbs, f"sbs_source_{idx}")
            #         if sbs_source_value:
            #             # Check if any discourse from the list is in the sbs_source_value
            #             for discourse in list_of_discourses:
            #                 if discourse in sbs_source_value:
            #                     if not i.sbs.discourses_source:
            #                         # Copy values to discourses fields
            #                         for field_prefix in ['source', 'sutta', 'example']:
            #                             sbs_value = getattr(i.sbs, f"sbs_{field_prefix}_{idx}")
            #                             setattr(i.sbs, f"discourses_{field_prefix}", sbs_value)
            #                         # print(f"{i.id} {sbs_value}")

            #                         # Change sbs_category to the lower letter version of the source
            #                         # Extract the part before the first full stop or use the whole if no full stop
            #                         old_category = i.sbs.sbs_category
            #                         category = discourse.split('.')[0].lower()
            #                         i.sbs.sbs_category = category
            #                         print(f"Updated category for {i.id} to {category} from {old_category}")

            #                         count += 1
            #                         break  # Stop checking other discourses if one is found

            # if not i.sbs:
            #     # Iterate over each source field
            #     for idx in range(1, 3):
            #         source_value = getattr(i, f"source_{idx}")
            #         if source_value and any(discourse in source_value for discourse in list_of_discourses) and i.meaning_1:
            #             # Create a new SBS object with the same id as the DpdHeadword
            #             new_sbs = SBS(id=i.id)
            #             db_session.add(new_sbs)
            #             # Copy values to discourses fields
            #             for field_prefix in ['source', 'sutta', 'example']:
            #                 value = getattr(i, f"{field_prefix}_{idx}")
            #                 setattr(new_sbs, f"discourses_{field_prefix}", value)

            #             # Change sbs_category to the lower letter version of the source
            #             # Extract the part before the first full stop or use the whole if no full stop
            #             category = source_value.split('.')[0].lower() + "_"
            #             new_sbs.sbs_category = category

            #             print(f"Updated category for {i.id} to {category}")
            #             if not i.ru:
            #                 print(f"no ru {i.id}")

            #             count += 1
                        
            #             db_session.commit()
            #             break  # Stop checking other discourses if one is found

            if i.sbs and not i.sbs.sbs_category:
                # Iterate over each source field
                for idx in range(1, 3):
                    source_value = getattr(i, f"source_{idx}")
                    if source_value and any(discourse in source_value for discourse in list_of_discourses) and i.meaning_1:
                        # Copy values to discourses fields
                        for field_prefix in ['source', 'sutta', 'example']:
                            value = getattr(i, f"{field_prefix}_{idx}")
                            setattr(i.sbs, f"discourses_{field_prefix}", value)

                        # Change sbs_category to the lower letter version of the source
                        # Extract the part before the first full stop or use the whole if no full stop
                        category = source_value.split('.')[0].lower() + "_"
                        i.sbs.sbs_category = category

                        print(f"Updated category for {i.id} to {category}")
                        if not i.ru:
                            print(f"no ru {i.id}")

                        count += 1
                        
                        break  # Stop checking other discourses if one is found

            # if i.sbs and not i.sbs.discourses_source:
            #     # Iterate over each source field
            #     for idx in range(1, 3):
            #         source_value = getattr(i, f"source_{idx}")
            #         if source_value and any(discourse in source_value for discourse in list_of_discourses) and i.meaning_1:
            #             # Copy values to discourses fields
            #             for field_prefix in ['source', 'sutta', 'example']:
            #                 value = getattr(i, f"{field_prefix}_{idx}")
            #                 setattr(i.sbs, f"discourses_{field_prefix}", value)

            #             # Change sbs_category to the lower letter version of the source
            #             # Extract the part before the first full stop or use the whole if no full stop
            #             old_category = i.sbs.sbs_category
            #             category = source_value.split('.')[0].lower() + "_"
            #             i.sbs.sbs_category = category

            #             print(f"Updated category for {i.id} to {category} from {old_category}")
            #             if not i.ru:
            #                 print(f"no ru {i.id}")

            #             count += 1
                        
            #             break  # Stop checking other discourses if one is found

        # Commit after processing all records
        # db_session.commit()
        print(f"Updated {count} records.")
        print("All changes committed.")


def moving_sbs_ex():
    with db_session.no_autoflush:
        for i in db:
            if i.sbs:
                if i.sbs.sbs_example_1 and not i.sbs.sbs_chapter_1 and not i.sbs.sbs_example_3:
                    # move from example_1 to example_3
                    i.sbs.sbs_example_3 = i.sbs.sbs_example_1
                    i.sbs.sbs_source_3 = i.sbs.sbs_source_1
                    i.sbs.sbs_sutta_3 = i.sbs.sbs_sutta_1

                    # clean example_1
                    i.sbs.sbs_example_1 = ""
                    i.sbs.sbs_source_1 = ""
                    i.sbs.sbs_sutta_1 = ""

                    print(f"{i.id} moved example_1 to example_3")

                    print(f"{i.id} {i.sbs.sbs_source_3}")


        # Commit after processing all records
        # db_session.commit()
        print("All changes committed.")


if __name__ == "__main__":
    # dhp()
    # pali_class()
    pat()
    # vib()
    # discor()