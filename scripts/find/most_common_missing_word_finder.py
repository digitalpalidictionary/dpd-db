"""Find most common words in a list, grouping by Levenshtein distance."""

from collections import Counter
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
        ):
            keep_list.append(book)
    pr.yes(len(keep_list))

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


def find_most_common_words(words: list[str]) -> list[tuple[str, int, set[str]]]:
    if not words:
        return []

    groups: list[list[str]] = []

    for word in track(words, description="[green]making groups"):  # , transient=True
        found_group = False
        for group in groups:
            representative = group[0]
            if (
                word[:3] == representative[:3]  # same starting letters
                and test_similar(word, representative)
                and Levenshtein.distance(word, representative) <= lev_distance
            ):
                group.append(word)
                found_group = True
                break
        if not found_group:
            groups.append([word])

    pr.green("making word_counts")
    # For each group, find the most common item to be the representative
    # and count the total number of items.
    word_counts = []
    for group in groups:
        if group:
            # Find the most common word in the group to act as the representative
            count = len(group)
            most_common_in_group = Counter(group).most_common(1)[0][0]
            word_counts.append((most_common_in_group, count, set(group)))

    # Sort by frequency
    word_counts.sort(key=lambda x: x[1], reverse=True)
    pr.yes(len(word_counts))

    return word_counts


def unpack_common_words(common_words):
    pr.green("making dict for tsv")
    common_words_unpack = []
    for i in common_words:
        word, count, word_list = i

        common_words_unpack.append(
            {
                "word": word,
                "count": count,
                "word list": word_list,
            }
        )
    pr.yes(len(common_words_unpack))
    return common_words_unpack


def save_to_tsv(common_words_unpack):
    pr.green("saving to tsv")

    file_path = Path("temp/most_common_missing_words.tsv")
    write_tsv_dot_dict(
        file_path,
        data=common_words_unpack,
    )
    pr.yes(len(common_words_unpack))
    pr.info(f"saved to: [white]{file_path}[/white]")


def main():
    pr.tic()
    pr.title("find most common missing words")

    commentary_books: list[str] = make_list_of_commentary_books()

    sandhi_checked_list = get_sandhi_checked_list()

    pr.green("making cst text list")
    commentary_words = make_cst_text_list(
        commentary_books,
        dedupe=False,
        show_errors=False,
    )
    pr.yes(len(commentary_words))

    dpd_inflections = get_dpd_inflections_set()

    commentary_words_reduced = reduce_commentary_words(
        commentary_words, dpd_inflections, sandhi_checked_list
    )

    common_words = find_most_common_words(
        commentary_words_reduced,
    )

    common_words_unpack = unpack_common_words(common_words)

    save_to_tsv(common_words_unpack)

    pr.toc()


if __name__ == "__main__":
    main()
