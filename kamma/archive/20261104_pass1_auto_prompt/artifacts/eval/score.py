"""Task 3.2: score the raw answers of Set G against the gold headwords.

Versions scored: old (old prompt re-sent), new (new prompt), hist (the saved
historic response in temp/prompts/pass1). Set K has no gold, so it only gets a
JSON-valid rate and an exact-keys rate.

cd <repo> && uv run kamma/threads/20261104_pass1_auto_prompt/artifacts/eval/score.py
Writes artifacts/eval/scores.csv and prints the summary tables."""

import csv
import json
import sys
from pathlib import Path

from sqlalchemy import select

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from gui2.pass1_context import ANSWER_KEYS
from tools.paths import ProjectPaths

sys.path.insert(0, "kamma/threads/20261104_pass1_auto_prompt/artifacts/eval")
from common import EVAL_DIR  # type: ignore  # noqa: E402

MODEL = "deepseek-v4-flash"
FIELDS = (
    "lemma_1",
    "pos",
    "root_key",
    "family_root",
    "family_compound",
    "construction",
    "stem",
    "pattern",
)
HIST_DIR = Path("temp/prompts/pass1")

db = get_db_session(ProjectPaths().dpd_db_path)


def parse(text: str) -> dict | None:
    cleaned = text.replace("```json\n", "").replace("```", "").strip()
    try:
        answer = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return answer if isinstance(answer, dict) else None


def gold_value(hw: DpdHeadword, field: str) -> str:
    value = hw.lemma_clean if field == "lemma_1" else getattr(hw, field)
    return (value or "").strip()


def match(answer: dict, hw: DpdHeadword) -> dict[str, int]:
    return {
        f: int(str(answer.get(f, "")).strip() == gold_value(hw, f)) for f in FIELDS
    }


def read_answer(set_name: str, version: str, word: str) -> str | None:
    if version == "hist":
        path = HIST_DIR / f"{word}_response"
    else:
        path = EVAL_DIR / "raw" / set_name / MODEL / version / f"{word}.txt"
    return path.read_text(encoding="utf-8") if path.exists() else None


words = json.loads((EVAL_DIR / "words.json").read_text(encoding="utf-8"))
rows: list[dict] = []

for set_name in ("G", "K"):
    versions = ("old", "new", "hist") if set_name == "G" else ("old", "new")
    for entry in words[set_name]:
        word = entry["word"]
        golds = (
            list(db.scalars(select(DpdHeadword).where(DpdHeadword.id.in_(entry["gold_ids"]))))
            if set_name == "G"
            else []
        )
        for version in versions:
            text = read_answer(set_name, version, word)
            if text is None:
                continue
            answer = parse(text)
            row: dict = {
                "set": set_name,
                "version": version,
                "word": word,
                "book": entry["book"],
                "had_sentence": entry.get("had_sentence", ""),
                "json_valid": int(answer is not None),
                "keys_exact": int(answer is not None and list(answer) == list(ANSWER_KEYS)),
            }
            if answer is not None and golds:
                parsed: dict = answer
                best = max(golds, key=lambda hw: sum(match(parsed, hw).values()))
                row.update(match(parsed, best))
                row["gold_lemma"] = best.lemma_1
            rows.append(row)

out = EVAL_DIR / "scores.csv"
columns = [
    "set", "version", "word", "book", "had_sentence", "json_valid", "keys_exact",
    *FIELDS, "gold_lemma",
]  # fmt: skip
with out.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)


def pct(num: int, den: int) -> str:
    return f"{100 * num / den:5.1f}" if den else "  n/a"


def table(title: str, subset_filter) -> None:
    print(f"\n{title}")
    print(f"{'version':8}{'n':>4}{'json%':>7}{'keys%':>7}" + "".join(f"{f[:9]:>10}" for f in FIELDS) + f"{'total%':>8}")
    for version in ("old", "new", "hist"):
        subset = [r for r in rows if r["set"] == "G" and r["version"] == version and subset_filter(r)]
        if not subset:
            continue
        n = len(subset)
        scored = [r for r in subset if "pos" in r]
        field_cells = "".join(
            f"{pct(sum(r[f] for r in scored), len(scored)):>10}" for f in FIELDS
        )
        total = sum(sum(r[f] for f in FIELDS) for r in scored)
        print(
            f"{version:8}{n:>4}{pct(sum(r['json_valid'] for r in subset), n):>7}"
            f"{pct(sum(r['keys_exact'] for r in subset), n):>7}{field_cells}"
            f"{pct(total, len(scored) * len(FIELDS)):>8}"
        )


table("Set G — all words", lambda r: True)
table("Set G — words that had NO sentence in the old prompt", lambda r: r["had_sentence"] is False)
table("Set G — words that had a sentence in the old prompt", lambda r: r["had_sentence"] is True)

print("\nSet K — JSON validity (no gold)")
for version in ("old", "new"):
    subset = [r for r in rows if r["set"] == "K" and r["version"] == version]
    n = len(subset)
    print(
        f"{version:8}{n:>4}{pct(sum(r['json_valid'] for r in subset), n):>7}"
        f"{pct(sum(r['keys_exact'] for r in subset), n):>7}"
    )
print(f"\nwrote {out}")
