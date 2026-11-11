"""Time DatabaseManager.get_all_lemma_1_and_lemma_clean() six times in one
process (a warm in-process cost, as it is after a save). Read-only on dpd.db.
Run from the repo root: PYTHONPATH=. uv run python /tmp/.../time_lemmas.py"""

import time

from gui2.database_manager import DatabaseManager  # noqa: E402

manager = DatabaseManager()
times: list[float] = []
for i in range(6):
    t0 = time.perf_counter()
    manager.get_all_lemma_1_and_lemma_clean()
    times.append(time.perf_counter() - t0)

for i, t in enumerate(times):
    print(f"run{i + 1} {t:.3f}")
