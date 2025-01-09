#!/usr/bin/env python3

"""
    Filter the database on a specified column by a given value, then replace some values in another specified column.
"""

from sqlalchemy.orm.attributes import InstrumentedAttribute

from db.models import DpdHeadword, SBS
from tools.paths import ProjectPaths
from db.db_helpers import get_db_session
from rich.console import Console

import re

console = Console()

def filter_and_replace(
        column_to_filter: InstrumentedAttribute, 
        filter_value: str,
        related_table,
        related_column_to_update: InstrumentedAttribute, 
        what_to_replace: str,
        replace_with: str
    ):
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # Find the words that match the filter criteria
    words_to_update = db_session.query(DpdHeadword, related_table).join(
        related_table, related_table.id == DpdHeadword.id
    ).filter(
        column_to_filter == filter_value,
        (related_column_to_update).contains(what_to_replace)
    ).all()

    for __word__, related in words_to_update:
        old_value = getattr(related, related_column_to_update.key)
        new_value = re.sub((what_to_replace), replace_with, old_value)

        setattr(related, related_column_to_update.key, new_value) 

        console.print(f"[bold bright_yellow]{__word__.id} {related_column_to_update.key}:")
        print()
        print(f"{old_value}")
        print()
        print(f"{new_value}")
        print()

    # db_session.commit()


column_to_filter = DpdHeadword.pos
filter_value = "idiom"
related_table = SBS
related_column_to_update = SBS.sbs_example_4
what_to_replace = "<b> </b>"
replace_with = " "

# !To use the function:
filter_and_replace(column_to_filter, filter_value, related_table, related_column_to_update, what_to_replace, replace_with)


