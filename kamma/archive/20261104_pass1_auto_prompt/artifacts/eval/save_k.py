"""Task 5.3: save the K-set answers of the new prompt into pass1_auto_{book}.json,
as the controller does: example/translation from the chosen sentences, the
[provider: model] comment prefix, unknown keys dropped. Never overwrites a key.

cd <repo> && uv run kamma/threads/20261104_pass1_auto_prompt/artifacts/eval/save_k.py"""

import json
import sys

from icecream import ic

from gui2.pass1_context import ANSWER_KEYS
from gui2.pass1_file_manager import Pass1FileManager
from gui2.paths import Gui2Paths

sys.path.insert(0, "kamma/threads/20261104_pass1_auto_prompt/artifacts/eval")
from context import EVAL_DIR, k_prompts, words  # type: ignore  # noqa: E402

PROVIDER = "deepseek"
MODEL = "deepseek-v4-flash"

manager = Pass1FileManager(Gui2Paths())
by_book: dict[str, dict[str, dict[str, str]]] = {}
skipped: list[str] = []

for entry in words()["K"]:
    raw_file = EVAL_DIR / "raw" / "K" / MODEL / "new" / f"{entry['word']}.txt"
    try:
        answer = json.loads(raw_file.read_text(encoding="utf-8").replace("```json\n", "").replace("```", ""))
    except (OSError, json.JSONDecodeError) as error:
        skipped.append(f"{entry['word']}: {error}")
        continue
    saved = {key: answer[key] for key in ANSWER_KEYS if key in answer}
    saved["comment"] = f"[{PROVIDER}: {MODEL}] {saved.get('comment', '')}"
    sentences = k_prompts(entry)[2]
    for count, (pali, english) in enumerate(sentences[:2], start=1):
        saved[f"example_{count}"] = pali
        saved[f"translation_{count}"] = english
    by_book.setdefault(entry["book_key"], {})[entry["word"]] = saved

for book, new_words in by_book.items():
    before = manager.read(book)
    manager.update(book, lambda data, nw=new_words: data.update({w: v for w, v in nw.items() if w not in data}))
    after = manager.read(book)
    assert all(after[w] == v for w, v in before.items()), f"old keys changed in {book}"
    print(f"{book}: before {len(before)}, after {len(after)}, offered {len(new_words)}")
ic(skipped)
