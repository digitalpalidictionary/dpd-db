"""Effect of reading the SuttaCentral list. No db is written.
Run: uv run kamma/threads/20261118_preview_inflection_table/artifacts/wordlist_effect_probe.py"""

import json
import random
from pathlib import Path

from db.db_helpers import get_db_session
from db.inflections.generate_inflection_tables import make_inflection_table
from db.models import DpdHeadword
from tools.all_tipitaka_words import make_all_tipitaka_word_set
from tools.paths import ProjectPaths

pth = ProjectPaths()
old: set[str] = set()
for path in (pth.cst_wordlist, pth.bjt_wordlist, pth.sya_wordlist, pth.sya_wordlist):
    old |= set(json.loads(path.read_text(encoding="utf-8")))
new = make_all_tipitaka_word_set()
print(f"set before {len(old)}, after {len(new)}, added {len(new - old)}")

session = get_db_session(Path("dpd.db"))
rows = session.query(DpdHeadword).filter(DpdHeadword.pattern != "").all()
sample = random.Random(7).sample(rows, 500)
changed = 0
for row in sample:
    if row.it is None or not row.it.data:
        continue
    before, _ = make_inflection_table(row, row.it, old)
    after, _ = make_inflection_table(row, row.it, new)
    changed += before != after
print(f"of 500 sampled tables, {changed} get different grey cells")
