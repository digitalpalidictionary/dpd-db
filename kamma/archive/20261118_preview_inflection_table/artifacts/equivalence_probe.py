"""make_inflection_table against the stored inflections_html. Run before the word-list fix.
Run: uv run kamma/threads/20261118_preview_inflection_table/artifacts/equivalence_probe.py"""

import random
from pathlib import Path

from db.db_helpers import get_db_session
from db.inflections.generate_inflection_tables import make_inflection_table
from db.models import DpdHeadword
from tools.all_tipitaka_words import make_all_tipitaka_word_set

session = get_db_session(Path("dpd.db"))
words = make_all_tipitaka_word_set()
rows = session.query(DpdHeadword).filter(DpdHeadword.pattern != "").all()
sample = random.Random(7).sample(rows, 500)
equal = 0
different: list[tuple[str, str]] = []
no_template = 0
for row in sample:
    if row.it is None or not row.it.data:
        no_template += 1
        continue
    html, _ = make_inflection_table(row, row.it, words)
    if html == row.inflections_html:
        equal += 1
    else:
        different.append((row.lemma_1, row.pattern))
print(f"sampled {len(sample)} of {len(rows)}: equal {equal}, different {len(different)}, no template {no_template}")
for lemma, pattern in different[:20]:
    print("  different:", lemma, pattern)
