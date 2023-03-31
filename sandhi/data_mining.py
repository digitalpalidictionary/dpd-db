from collections import Counter

import csv
from pathlib import Path
import re

do_unmatched_path = Path("sandhi/output_do/unmatched.csv")
do_unmatched_groups_path = Path("sandhi/output/mining/unmatched_groups.tsv")
do_unmatched_groups_path.parent.mkdir(parents=True, exist_ok=True)

do_matches_path = Path("sandhi/output_do/matches.csv")
do_matches_pairs_path = Path("sandhi/output/mining/matches_pairs.tsv")

tipitaka_word_freq = Path("frequency/output/word_count/tipitaka.csv")
umatched_freq_path = Path("sandhi/output/mining/umatched_freq.tsv")


def mine_unmatched():
    with open(do_unmatched_path)as f:
        reader = csv.reader(f)
        do_unmatched: list = [row[0] for row in reader]

    groups = {}
    for word in do_unmatched:
        for i in range(len(word)-5):
            for j in range(i+6, len(word)+1):  # iterate over all possible group lengths from 4 to len(word)
                group = word[i:j]
                if len(group) < 4:  # skip groups shorter than 4 letters
                    continue
                if group in groups:
                    groups[group].append(word)
                else:
                    groups[group] = [word]

    sorted_groups = sorted(
        groups.items(), key=lambda x: len(x[1]), reverse=True)

    with open(do_unmatched_groups_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(['Count', 'Group', 'Words'])
        for group, words in sorted_groups:
            if len(words) > 10:
                writer.writerow([len(words), group, ', '.join(words)])


def mine_matches():
    with open(do_matches_path)as f:
        reader = csv.reader(f, delimiter="\t")
        do_matches: list = [row[1] for row in reader]

    word_pairs = Counter()
    for pattern in do_matches:
        pairs = re.findall(r"\b\w+\b \+ \b\w+\b", pattern)
        for pair in pairs:
            word_pairs[pair] += 1

    with open(do_matches_pairs_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(['count', 'pair'])
        for pair, count in word_pairs.most_common():
            writer.writerow([count, pair])


def unmatched_frequency():
    tipitaka_freq: dict = {}
    with open(tipitaka_word_freq) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            tipitaka_freq[row[0]] = int(row[1])

    with open(do_unmatched_path)as f:
        reader = csv.reader(f)
        do_unmatched: list = [row[0] for row in reader]

    unmatched_freq: dict = {}
    for word in do_unmatched:
        try:
            unmatched_freq[word] = tipitaka_freq[word]
        except:
            pass
            # print(f"{word} doesnt exist")

    unmatched_freq_sorted = [(k, v) for k, v in sorted(
        unmatched_freq.items(), key=lambda item: item[1], reverse=True)]

    with open(umatched_freq_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["unmatched_word", "count"])
        for i in unmatched_freq_sorted:
            writer.writerow([i[0], i[1]])


mine_unmatched()
mine_matches()
unmatched_frequency()
