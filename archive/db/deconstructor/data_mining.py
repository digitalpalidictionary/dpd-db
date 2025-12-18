"""Data mining the deconstructor results."""

from collections import Counter

import csv
from pathlib import Path
import re

do_unmatched_path = Path("db/deconstructor/output_do/unmatched.tsv")
do_unmatched_groups_path = Path("db/deconstructor/output/mining/unmatched_groups.tsv")
do_unmatched_groups_path.parent.mkdir(parents=True, exist_ok=True)

do_matches_path = Path("db/deconstructor/output_do/matches.tsv")
do_matches_pairs_path = Path("db/deconstructor/output/mining/matches_pairs.tsv")

tipitaka_word_freq = Path("db/frequency/output/word_count/tipitaka.csv")
tipitaka_umatched_freq_path = Path(
    "db/deconstructor/output/mining/umatched_freq_tipitaka.tsv"
)

ebts_word_freq = Path("db/frequency/output/word_count/ebts.csv")
ebts_umatched_freq_path = Path("db/deconstructor/output/mining/umatched_freq_ebts.tsv")


def mine_unmatched():
    with open(do_unmatched_path) as f:
        reader = csv.reader(f)
        do_unmatched: list = [row[0] for row in reader]

    groups = {}
    for word in do_unmatched:
        for i in range(len(word) - 5):
            # iterate over all possible group lengths from 4 to len(word)
            for j in range(i + 6, len(word) + 1):
                group = word[i:j]
                if len(group) < 4:  # skip groups shorter than 4 letters
                    continue
                if group in groups:
                    groups[group].append(word)
                else:
                    groups[group] = [word]

    sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)

    with open(do_unmatched_groups_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Count", "Group", "Words"])
        for group, words in sorted_groups:
            if len(words) > 10:
                writer.writerow([len(words), group, ", ".join(words)])


def mine_matches():
    with open(do_matches_path) as f:
        reader = csv.reader(f, delimiter="\t")
        do_matches: list = [row[1] for row in reader]

    word_pairs = Counter()
    for pattern in do_matches:
        pairs = re.findall(r"\b\w+\b \+ \b\w+\b", pattern)
        for pair in pairs:
            word_pairs[pair] += 1

    with open(do_matches_pairs_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["count", "pair"])
        for pair, count in word_pairs.most_common():
            writer.writerow([count, pair])


def tipitaka_unmatched_frequency():
    tipitaka_freq: dict = {}
    with open(tipitaka_word_freq) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            tipitaka_freq[row[0]] = int(row[1])

    with open(do_unmatched_path) as f:
        reader = csv.reader(f)
        do_unmatched: list = [row[0] for row in reader]

    tipitaka_unmatched_freq: dict = {}
    for word in do_unmatched:
        try:
            tipitaka_unmatched_freq[word] = tipitaka_freq[word]
        except KeyError:
            pass
            # print(f"{word} doesnt exist")

    tipitaka_unmatched_freq_sorted = [
        (k, v)
        for k, v in sorted(
            tipitaka_unmatched_freq.items(), key=lambda item: item[1], reverse=True
        )
    ]

    with open(tipitaka_umatched_freq_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["unmatched_word", "count"])
        for i in tipitaka_unmatched_freq_sorted:
            writer.writerow([i[0], i[1]])


def ebts_unmatched_frequency():
    ebts_freq: dict = {}
    with open(ebts_word_freq) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            ebts_freq[row[0]] = int(row[1])

    with open(do_unmatched_path) as f:
        reader = csv.reader(f)
        do_unmatched: list = [row[0] for row in reader]

    ebts_unmatched_freq: dict = {}
    for word in do_unmatched:
        try:
            ebts_unmatched_freq[word] = ebts_freq[word]
        except KeyError:
            pass
            # print(f"{word} doesnt exist")

    ebts_unmatched_freq_sorted = [
        (k, v)
        for k, v in sorted(
            ebts_unmatched_freq.items(), key=lambda item: item[1], reverse=True
        )
    ]

    with open(ebts_umatched_freq_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["unmatched_word", "count"])
        for i in ebts_unmatched_freq_sorted:
            writer.writerow([i[0], i[1]])


mine_unmatched()
mine_matches()
tipitaka_unmatched_frequency()
ebts_unmatched_frequency()
