"""Find most common words in a list, grouping by Levenshtein distance."""

from pathlib import Path

import Levenshtein
from rich.progress import track

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.cst_sc_text_sets import make_cst_text_list
from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_single_column, write_tsv_dot_dict

pth = ProjectPaths()

similarity = 3
lev_distance = 3


def make_list_of_commentary_books() -> list[str]:
    pr.green("making book list")
    done_list = [
        "vin1",
        "vin2",
        "vin3",
        "vin4",
        "dn1",
        "dn2",
        "dn3",
        "mn1",
        "mn2",
        "mn3",
        "sn1",
        "sn2",
        "sn3",
        "sn4",
        "sn5",
        "an1",
        "an2",
        "an3",
        "an4",
        "an5",
        "an6",
        "an7",
        "an8",
        "an9",
        "an10",
        "an11",
        "kn1",
        "kn2",
        "kn3",
        "kn4",
        "kn5",
        "kn8",
        "kn9",
    ]
    anna_list = ["anna"]
    keep_list = []
    for book in cst_texts:
        if (
            book not in done_list
            and not book.startswith("abh")
            # and not book.endswith("a")
            and not book.endswith("t")
            and book not in anna_list
            and not book.startswith("kn")
            and not book.startswith("ap")
            and not book.startswith("vism")
        ):
            keep_list.append(book)
    pr.yes(len(keep_list))
    print(keep_list)

    return keep_list
    # return ["kn15", "kn16"]


def get_dpd_inflections_set() -> set[str]:
    pr.green("making dpd inflections set")

    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    inflections_set: set[str] = set()
    for i in db:
        for word in i.inflections_list_all:
            inflections_set.add(word)
    pr.yes(len(inflections_set))

    return inflections_set


def get_sandhi_checked_list():
    return read_tsv_single_column(pth.decon_checked)


def get_list_of_cst_words_in_books(commentary_books):
    pr.green("making cst text list")
    cst_word_list = make_cst_text_list(
        commentary_books,
        dedupe=False,
        show_errors=False,
    )
    pr.yes(len(cst_word_list))
    return cst_word_list


def reduce_commentary_words(
    commentary_words,
    dpd_inflections,
    sandhi_checked_list,
):
    pr.green("reducing word set")
    commentary_words_reduced = []
    dpd_inflections_set = set(dpd_inflections)
    sandhi_checked_set = set(sandhi_checked_list)
    for word in commentary_words:
        if word not in dpd_inflections_set and word not in sandhi_checked_set:
            commentary_words_reduced.append(word)
    pr.yes(len(commentary_words_reduced))
    return commentary_words_reduced


def make_word_count_dict(cst_word_list_reduced: list[str]) -> dict[str, int]:
    """Return a dict of words and their counts"""

    pr.green("making word count dict")

    word_count_dict: dict[str, int] = {}
    for i in cst_word_list_reduced:
        if i not in word_count_dict:
            word_count_dict[i] = 1
        else:
            word_count_dict[i] += 1

    pr.yes(len(word_count_dict))

    return word_count_dict


def test_similar(word: str, representative: str):
    if word == representative:
        return True

    word_len = len(word)
    repr_len = len(representative)
    diff_len = word_len - repr_len

    word_trunc = word[:-similarity]
    repr_trunc = representative[: -similarity + diff_len]

    if word_trunc == repr_trunc:
        return True
    else:
        return False


def group_similar_words(
    words: dict[str, int],
) -> dict[dict[str, int], dict[str, set[str]]]:
    if not words:
        return {}

    # {taṅhā: {"count":212, "members":{"taṅhā", "taṅhāti", taṅhāyāpi"}}}
    groups = {}

    for word, count in track(words.items(), description="[green]grouping"):
        found_group = False
        for representative, data in groups.items():
            if (
                word[:4] == representative[:4]  # same starting letters
                and test_similar(word, representative)
                and Levenshtein.distance(word, representative) <= lev_distance
            ):
                groups[representative]["count"] += count
                groups[representative]["members"].add(word)
                found_group = True
                break
        if not found_group:
            groups[word] = {"representative": word, "count": count, "members": {word}}
    return groups


def sort_groups(
    groups: dict[dict[str, int], dict[str, set[str]]],
) -> list:
    group_list = []
    for key, values in groups.items():
        group_list.append(values)

    return sorted(group_list, key=lambda x: x["count"], reverse=True)


def save_to_tsv(common_words_unpack):
    pr.green("saving to tsv")

    file_path = Path("scripts/find/most_common_missing_words.tsv")
    write_tsv_dot_dict(
        file_path,
        data=common_words_unpack,
    )
    pr.yes(len(common_words_unpack))
    pr.info(f"saved to: [white]{file_path}[/white]")


def main():
    pr.tic()
    pr.title("find most common missing words")
    commentary_books = make_list_of_commentary_books()
    sandhi_checked_list = get_sandhi_checked_list()
    cst_word_list = get_list_of_cst_words_in_books(commentary_books)
    dpd_inflections_set = get_dpd_inflections_set()
    cst_word_list_reduced = reduce_commentary_words(
        cst_word_list,
        dpd_inflections_set,
        sandhi_checked_list,
    )
    word_count_dict = make_word_count_dict(cst_word_list_reduced)
    groups = group_similar_words(word_count_dict)
    sorted_groups = sort_groups(groups)
    save_to_tsv(sorted_groups)
    pr.toc()


if __name__ == "__main__":
    main()
