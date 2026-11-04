"""Task 1.4 follow-up: which stem length after the cut still finds the right PEU headword."""

import random
from collections import defaultdict

from tools.epitaka_sentences import peu_entries

from common import TARGET_BOOKS, MissingChecker  # type: ignore

checker = MissingChecker()
by_stem: defaultdict[int, list[tuple[str, int, str]]] = defaultdict(list)
total = 0
for ep_book, (book_key, cst_books) in TARGET_BOOKS.items():
    for w in checker.missing_words(book_key, cst_books):
        total += 1
        for cut in range(0, 4):
            hits = peu_entries(w, max_cut=cut)
            if hits:
                if cut:
                    by_stem[min(len(w) - cut, 8)].append((w, cut, hits[0][:70]))
                break
print("missing words:", total)
for n in sorted(by_stem):
    print(f"stem length {n}{'+' if n == 8 else ''}: {len(by_stem[n])} hits")
random.seed(2)
for n in (4, 5, 6, 7, 8):
    print(f"\n--- 10 samples, stem length {n}")
    for w, cut, hit in random.sample(by_stem[n], min(10, len(by_stem[n]))):
        print(f"- {w} | cut {cut} | {hit}")
