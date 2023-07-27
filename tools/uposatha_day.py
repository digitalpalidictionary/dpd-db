from datetime import date
from tools.configger import config_update

"""Dictionary releases are on full moon updatha days.
Modules for testing whether today is an updatha day and
saving the db count on uposatha day."""


def uposatha_today():
    """"Test whether today is an uposatha day and return a bool."""
    TODAY = date.today()

    uposathas = [
        date(2023, 1, 6),
        date(2023, 2, 5),
        date(2023, 3, 6),
        date(2023, 4, 5),
        date(2023, 5, 4),
        date(2023, 6, 3),
        date(2023, 7, 2),
        date(2023, 8, 1),
        date(2023, 8, 31),
        date(2023, 9, 29),
        date(2023, 10, 29),
        date(2023, 11, 27),
        date(2023, 12, 27),
        ]

    if TODAY in uposathas:
        return True
    else:
        return False


# print(uposatha_day())


def uposatha_count(value: int):
    """Save the PaliWord count on uposatha day."""
    config_update("uposatha", "count", str(value))


# uposatha_count(74657)
