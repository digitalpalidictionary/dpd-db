#!/usr/bin/env python3

"""
    Filter the database on a specified column by a given value, then update another specified column with a provided value.
"""

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import aliased

from db.models import PaliWord, SBS
from tools.paths import ProjectPaths
from db.get_db_session import get_db_session


def filter_and_update(
        column_to_filter: InstrumentedAttribute, 
        filter_value: str,
        related_class,
        related_column_to_update: InstrumentedAttribute, 
        update_value: str
    ):
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    
    # Create an alias for the related class to query it directly
    related_alias = aliased(related_class)

    # Find the words that match the filter criteria
    words_to_update = db_session.query(PaliWord, related_alias).join(
        related_alias, related_alias.id == PaliWord.id
    ).filter(column_to_filter == filter_value).all()

    for __word__, related in words_to_update:
        old_value = getattr(related, related_column_to_update.key)

        setattr(related, related_column_to_update.key, update_value)  

        print(f"{related_column_to_update.key}: {old_value} > {update_value}")

    # db_session.commit()


field_to_filter = PaliWord.pos
value_to_filter = "prefix"
table_to_update = SBS
field_to_update = SBS.sbs_category
value_to_update = ""

# !To use the function:
filter_and_update(field_to_filter, value_to_filter, table_to_update, field_to_update, value_to_update)


