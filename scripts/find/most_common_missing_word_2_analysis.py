"""Report coverage stats on the missing-word TSV produced by the `_1_finder` script.

Shows how many words are needed to cover successive occurrence-count
milestones, and what percentage of total occurrences is covered every 5000
words.
"""

from typing import Any

from rich import print

from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dict


def open_file() -> list[dict[str, Any]]:
    """Load the current missing-words TSV, falling back to the old one."""
    pth = ProjectPaths()
    try:
        return read_tsv_dict(str(pth.most_common_missing_words_tsv_path))
    except FileNotFoundError:
        return read_tsv_dict("scripts/find/most_common_missing_words_old.tsv")


def get_stats(data: list[dict[str, Any]]) -> dict[Any, Any]:
    """Return the word-index at which running occurrence totals cross fixed milestones."""
    total_dict: dict[Any, Any] = {}
    total_dict["word#"] = "total"
    running_total = 0
    k25000 = True
    k50000 = True
    k100000 = True
    k250000 = True
    for num, i in enumerate(data):
        running_total += int(i["count"])
        if k25000 and running_total > 25000:
            total_dict[num] = 25000
            k25000 = False
        if k50000 and running_total > 50000:
            total_dict[num] = 50000
            k50000 = False
        if k100000 and running_total > 100000:
            total_dict[num] = 100000
            k100000 = False
        if k250000 and running_total > 250000:
            total_dict[num] = 250000
            k250000 = False
    total_dict[num] = running_total

    return total_dict


def get_stats2(data: list[dict[str, Any]]) -> dict[int, float]:
    """Return the running percentage of total occurrences covered every 5000 words."""
    total_dict: dict[int, float] = {}
    running_total = 0
    for num, i in enumerate(data):
        running_total += int(i["count"])
    total = running_total

    running_total = 0

    for num, i in enumerate(data):
        running_total += int(i["count"])
        if num % 5000 == 0:
            total_dict[num] = (running_total / total) * 100

    total_dict[num] = 100.00
    return total_dict


def main() -> None:
    """Print coverage-milestone and percentage-coverage stats for the missing-words TSV."""
    data = open_file()

    totals_dict = get_stats(data)
    for k, v in totals_dict.items():
        print(f"{k:>6}: {v:>6}")

    print()

    totals_dict2 = get_stats2(data)
    for k, v in totals_dict2.items():
        print(f"{k:>6}: {v:>6.2f}")


if __name__ == "__main__":
    main()
