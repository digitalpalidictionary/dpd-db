from collections import Counter

import csv
from pathlib import Path
import re

do_unmatched_path = Path("sandhi/output_do/unmatched.csv")
do_unmatched_groups_path = Path("sandhi/output/mining/unmatched_groups.csv")
do_unmatched_groups_path.parent.mkdir(parents=True, exist_ok=True)

do_matches_path = Path("sandhi/output_do/matches.csv")
do_matches_pairs_path = Path("sandhi/output/mining/matches_pairs.csv")


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
        writer = csv.writer(f)
        writer.writerow(['Count', 'Group', 'Words'])
        for group, words in sorted_groups:
            if len(words) > 10:
                writer.writerow([len(words), group, ', '.join(words)])


# mine_unmatched()


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
        writer = csv.writer(f)
        writer.writerow(['Count', 'Group', 'Words'])
        for pair, count in word_pairs.most_common():
            writer.writerow([count, pair])


mine_matches()
