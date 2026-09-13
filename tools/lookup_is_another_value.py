"""Test whether a Lookup table row has values in other columns.
Used by db/lookup/ and tools/lookup_sync.py to decide if a row can be safely deleted."""

from db.models import Lookup

# Transliterations are derived from lookup_key, not content in their own right.
# Counting them keeps an emptied row alive forever and re-qualifies it for
# transliteration on every run.
TRANSLITERATION_COLUMNS = ("sinhala", "devanagari", "thai")


def is_another_value(row: Lookup, column_name: str) -> bool:
    """
    Test whether any other columns in the Lookup table have a value.
    It is used to determine whether a row in the Lookup table can be safely deleted or not.
    """

    for column in Lookup.__table__.columns:
        if column.name not in ("lookup_key", column_name, *TRANSLITERATION_COLUMNS):
            if getattr(row, column.name):
                return True
    return False
