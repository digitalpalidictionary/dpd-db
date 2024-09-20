import configparser
from datetime import date

from rich import print

from tools.paths import ProjectPaths

"""Dictionary releases are on full moon uposatha days.
Modules for testing whether today is an uposatha day and
saving the db count on uposatha day."""


def uposatha_today():
    """Test whether today is an uposatha day and return a bool."""
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
        date(2024, 1, 26),
        date(2024, 2, 24),
        date(2024, 3, 24),
        date(2024, 4, 23),
        date(2024, 5, 22),
        date(2024, 6, 21),
        date(2024, 7, 20),
        date(2024, 8, 19),
        date(2024, 9, 17),
        date(2024, 10, 17),
        date(2024, 11, 15),
        date(2024, 12, 15),
    ]

    def print_diff():
        for i in range(len(uposathas) - 1):
            diff = uposathas[i + 1] - uposathas[i]
            print(
                f"The difference between {uposathas[i]} and {uposathas[i+1]} is {diff.days} days."
            )

    # print_diff()

    if TODAY in uposathas:
        return True
    else:
        return False


def write_uposatha_count(new_value: int):
    """Save the DpdHeadword count on uposatha day."""

    pth = ProjectPaths()
    config = configparser.ConfigParser()
    config.read(pth.uposatha_day_ini)
    config.set("uposatha", "count", str(new_value))
    with open(pth.uposatha_day_ini, "w") as f:
        config.write(f)


def read_uposatha_count():
    """Read the DpdHeadword count from the last uposatha day."""

    pth = ProjectPaths()
    config = configparser.ConfigParser()
    config.read(pth.uposatha_day_ini)
    return config.get("uposatha", "count")


if __name__ == "__main__":
    print(uposatha_today())
    print(read_uposatha_count())
    # write_uposatha_count(78807)
