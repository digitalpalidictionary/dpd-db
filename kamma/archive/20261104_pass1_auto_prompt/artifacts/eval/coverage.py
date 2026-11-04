"""Task 1.4: ePitaka-sentence and PEU coverage of the missing words in the target books."""

import random

from gui2.books import sutta_central_books
from tools.epitaka_sentences import epitaka_word_dict, peu_entries

from common import TARGET_BOOKS, MissingChecker, cst_file_stems  # type: ignore

checker = MissingChecker()
rows = []
peu_hits: list[tuple[str, str, int, str]] = []
for ep_book, (book_key, cst_books) in TARGET_BOOKS.items():
    missing = checker.missing_words(book_key, cst_books)
    ep = epitaka_word_dict(cst_file_stems(cst_books))
    sc = sutta_central_books[book_key].word_dict if book_key in sutta_central_books else {}
    n = len(missing)
    sc_n = sum(1 for w in missing if sc.get(w))
    ep_n = sum(1 for w in missing if ep.get(w))
    any_n = sum(1 for w in missing if sc.get(w) or ep.get(w))
    peu_n = 0
    for w in missing:
        for cut in range(0, 4):
            hits = peu_entries(w, max_cut=cut)
            if hits:
                peu_n += 1
                peu_hits.append((ep_book, w, cut, hits[0][:90]))
                break
    pct = lambda x: f"{100 * x / n:.0f}%" if n else "-"  # noqa: E731
    rows.append((ep_book, n, pct(sc_n), pct(ep_n), pct(any_n), pct(peu_n)))

print("| book | missing words | ≥1 SC sentence (old) | ≥1 ePitaka sentence | ≥1 sentence (new) | ≥1 PEU entry |")
print("|---|---|---|---|---|---|")
for r in rows:
    print("| " + " | ".join(str(x) for x in r) + " |")

from collections import Counter  # noqa: E402

print("\nPEU cut used:", Counter(c for _, _, c, _ in peu_hits))
random.seed(20261104)
print("\n20 random PEU matches:")
for ep_book, w, cut, hit in random.sample(peu_hits, 20):
    print(f"- {ep_book} | {w} | cut {cut} | {hit}")
