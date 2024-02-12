#!/usr/bin/env python3

"""
    Filter the database on a specified column by a given value, then update another specified column with a provided value.
"""

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import aliased

from db.models import DpdHeadwords, SBS
from tools.paths import ProjectPaths
from db.get_db_session import get_db_session

from rich.console import Console

console = Console()


def filter_and_update(
        column_to_filter: InstrumentedAttribute, 
        filter_value: str,
        related_table,
        related_column_to_update: InstrumentedAttribute, 
        update_value: str
    ):
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    
    # Create an alias for the related class to query it directly
    related_alias = aliased(related_table)

    # Find the words that match the filter criteria
    words_to_update = db_session.query(DpdHeadwords, related_alias).join(
        related_alias, related_alias.id == DpdHeadwords.id
    ).filter(column_to_filter == filter_value).all()

    for __word__, related in words_to_update:
        old_value = getattr(related, related_column_to_update.key)
        if old_value or update_value:

            setattr(related, related_column_to_update.key, update_value)  

            console.print(f"[bold bright_yellow]{__word__.id} {related_column_to_update.key}:")
            print()
            print(f"{old_value}")
            print()
            print(f"{update_value}")
            print()

    # db_session.commit()


column_to_filter = DpdHeadwords.pos
filter_value = "prefix"
related_table = SBS
related_column_to_update = SBS.sbs_category
value_to_update = ""

# !To use the function:
filter_and_update(column_to_filter, filter_value, related_table, related_column_to_update, value_to_update)


