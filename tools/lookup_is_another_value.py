from db.models import Lookup


def is_another_value(row: Lookup, column_name: str) -> bool:
    """
    Test whether any other columns in the Lookup table have a value.
    It is used to determine whether a row in the Lookup table can be safely deleted or not.
    """

    for column in Lookup.__table__.columns:
        if column.name not in ["lookup_key", column_name]:
            if getattr(row, column.name):
                return True
    return False
