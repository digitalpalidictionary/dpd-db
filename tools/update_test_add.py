"""Test what to update, test or delete when using the lookup table"""

from db.models import Lookup


def update_test_add(
    lookup_table: list[Lookup], the_dict: dict
) -> tuple[set[str], set[str], set[str]]:
    """Input a db_session and a dictionary.
    Return three sets:
    1. update_set = all words in the Lookup table & dict
    2. test_set = All words only in the Lookup table
    3. add_set = All words only in the Lookup table - dict
    """

    # FIXME use four lists: add update clear delete

    # keys of the dict
    dict_keys = set([key for key in the_dict])

    # keys of the Lookup table
    lookup_keys = set([i.lookup_key for i in lookup_table])

    update_set: set[str] = dict_keys & lookup_keys
    test_set: set[str] = lookup_keys - dict_keys
    add_set: set[str] = dict_keys - lookup_keys

    return (update_set, test_set, add_set)
