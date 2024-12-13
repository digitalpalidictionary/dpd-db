#!/usr/bin/env python3

"""
    Filter the database on a specified column by a given value, then update another specified column with a provided value.
"""
import re

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import aliased
from sqlalchemy import and_, or_, null, not_
from sqlalchemy import update
from sqlalchemy.orm import joinedload

from db.models import DpdHeadword, SBS, Russian
from tools.paths import ProjectPaths
from db.db_helpers import get_db_session

from rich.console import Console

console = Console()

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

def filter_and_update(
        column_to_filter: InstrumentedAttribute, 
        filter_value: str,
        related_table,
        related_column_to_update, 
        update_value: str
    ):
    
    # Create an alias for the related class to query it directly
    related_alias = aliased(related_table)

    # Find the words that match the filter criteria
    words_to_update = db_session.query(DpdHeadword, related_alias).join(
        related_alias, related_alias.id == DpdHeadword.id
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



def filter_and_add(
        column_to_filter: InstrumentedAttribute,  
        filter_value: str,
        related_table,
        related_column_to_update,  
        update_value: str
    ):
    
    # Create an alias for the related class to query it directly
    related_alias = aliased(related_table)

    # Find the words that match the filter criteria
    words_to_update = db_session.query(DpdHeadword, related_alias).join(
        related_alias, related_alias.id == DpdHeadword.id
    ).filter(
        and_(
            column_to_filter.contains(filter_value),
            related_alias.ru_meaning_raw != "",
            related_alias.ru_meaning_raw.notlike(f'%{update_value}%'),
        )
    ).all()

    for __word__, related in words_to_update:
        old_value = getattr(related, related_column_to_update.key)
        if old_value or update_value:
            # Prepend (грам) to the existing value of ru_meaning_raw
            new_value = "(грам) " + old_value if old_value else update_value
            setattr(related, related_column_to_update.key, new_value)   

            console.print(f"[bold bright_yellow]{__word__.id} {related_column_to_update.key}:")
            print()
            print(f"{old_value}")
            print()
            print(f"{new_value}")
            print()

    # db_session.commit()


def update_notes():

    # "Kacc %" "see %" "or %"
    db = db_session.query(DpdHeadword).outerjoin(
    Russian, DpdHeadword.id == Russian.id
        ).filter(
            DpdHeadword.notes.like("agent noun used verbally see Perniola §292"),
        ).order_by(DpdHeadword.ebt_count.desc()).all()

    for counter, i in enumerate(db):

        # new_value = re.sub(r'\bor \b', 'или ', i.notes)
        new_value = re.sub("agent noun used verbally see Perniola §292", 'существительное деятель, используемое глагольно, см. Перниола §292', i.notes)
        # new_value = i.notes
        
        # Check if a Russian row with the same id exists
        existing_russian = db_session.query(Russian).filter(Russian.id == i.id).first()
        if not existing_russian:
            # If not, create a new Russian row
            new_russian = Russian(id=i.id, ru_notes=new_value)
            db_session.add(new_russian)
            console.print(f"[bold bright_yellow]{i.id} {Russian.ru_notes}:")
            print()
            print(f"{new_value}")
            print()

        else:
            old_value = getattr(i.ru, 'ru_notes')
            if "ИИ" in old_value or not old_value:
                # If it exists, use the existing row
                existing_russian.ru_notes = new_value

                console.print(f"[bold bright_yellow]{i.id} {Russian.ru_notes}:")
                print()
                print(f"{old_value}")
                print()
                print(f"{new_value}")
                print()

        # db_session.commit()


def update_column_for_some_criteria(source_value):
    # Query the database to find the rows that match the conditions
    rows_to_update_sbs = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).outerjoin(SBS).filter(
            or_(
                SBS.sbs_source_1 == source_value,
                SBS.sbs_source_2 == source_value,
                SBS.sbs_source_3 == source_value,
                SBS.sbs_source_4 == source_value,
            ),
    ).all()

    # Get the IDs of rows_to_update_sbs
    ids_to_exclude = [row.id for row in rows_to_update_sbs]


    rows_to_update = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).outerjoin(SBS).filter(
            and_(
                not_(DpdHeadword.id.in_(ids_to_exclude)),
                or_(
                    DpdHeadword.source_1 == source_value,
                    DpdHeadword.source_2 == source_value,
                ),
            ),
    ).all()

    count_changed = 0
    count_changed_sbs = 0
    count_added = 0
    count_sbs_patimokkha = 0

    for __word__ in rows_to_update_sbs:
        old_value = __word__.sbs.sbs_patimokkha
        if not old_value:
            __word__.sbs.sbs_patimokkha = "vib"

            console.print(f"[bold bright_yellow]{__word__.id} {__word__.lemma_1} {__word__.sbs.sbs_patimokkha}")

            count_changed_sbs += 1
        else:
            count_sbs_patimokkha += 1

    for __word__ in rows_to_update:
        if not __word__.sbs:
            # If SBS row does not exist, create a new one
            __word__.sbs = SBS(id=__word__.id, sbs_patimokkha="vib_")
            console.print(f"[bold bright_yellow]Added {__word__.id} {__word__.lemma_1} {__word__.sbs.sbs_patimokkha}")
            count_added += 1
        else:
            old_value = __word__.sbs.sbs_patimokkha
            if not old_value:
                __word__.sbs.sbs_patimokkha = "vib_"

                console.print(f"[bold bright_yellow]{__word__.id} {__word__.lemma_1} {__word__.sbs.sbs_patimokkha}")

                count_changed += 1
            else:
                count_sbs_patimokkha += 1



    console.print(f"[bold bright_green]Total rows fit criteria sbs: {len(rows_to_update_sbs)}")
    console.print(f"[bold bright_green]Total rows fit criteria: {len(rows_to_update)}")
    console.print(f"[bold bright_green]Total count of already has: {count_sbs_patimokkha}")
    console.print(f"[bold bright_green]Total count of changed: {count_changed}")
    console.print(f"[bold bright_green]Total count of changed sbs: {count_changed_sbs}")
    console.print(f"[bold bright_green]Total count of added: {count_added}")

    # db_session.commit()


column_to_filter = DpdHeadword.meaning_1
filter_value = "(gram)"
related_table = Russian
related_column_to_update = "ru_meaning_raw"
value_to_update = "(грам) "

# !To use the functions:

# filter_and_update(column_to_filter, filter_value, related_table, related_column_to_update, value_to_update)

# filter_and_add(column_to_filter, filter_value, related_table, related_column_to_update, value_to_update)

# update_notes()

update_column_for_some_criteria("VIN1.2.2")
