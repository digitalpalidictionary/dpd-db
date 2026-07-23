"""AI-Powered Dictionary Proofreading System.

Proofreads three fields, each into its own queue TSV + incremental cache:

- ``meaning_1``   — every entry with a non-empty meaning_1.
- ``meaning_lit`` — every entry with a non-empty meaning_lit; the prompt is fed
  the entry's meaning_1 as read-only context, because meaning_lit is a
  deliberately literal gloss that must NOT be made more idiomatic.
- ``meaning_2``   — only entries where meaning_1 is empty (meaning_2 is then the
  primary meaning).

Each field keeps an id -> last-checked-source-text cache so re-runs only
re-proofread entries whose source text changed.
"""

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from filelock import FileLock
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.ai_manager import AIManager, AIResponse
from tools.paths import ProjectPaths
from tools.printer import printer as pr


@dataclass
class ProofreadField:
    """One proofreading pass: which DB field, where its queue/cache live, and
    how to build its prompt."""

    name: str
    tsv_path: Path
    cache_path: Path
    context_field: str | None = None
    only_empty_meaning_1: bool = False


def get_db_data(
    db_session: Session,
    field: str = "meaning_1",
    context_field: str | None = None,
    only_empty_meaning_1: bool = False,
) -> list[dict[str, Any]]:
    """Query DpdHeadword for entries with a non-empty ``field``.

    ``context_field`` (e.g. meaning_1 for a meaning_lit pass) is included in each
    row so the prompt can show it as read-only context. ``only_empty_meaning_1``
    restricts the pass to entries whose meaning_1 is empty.
    """
    column = getattr(DpdHeadword, field)
    query = db_session.query(DpdHeadword).filter(column != "")
    if only_empty_meaning_1:
        query = query.filter(DpdHeadword.meaning_1 == "")

    rows: list[dict[str, Any]] = []
    for r in query.all():
        row: dict[str, Any] = {
            "id": r.id,
            "lemma_1": r.lemma_1,
            field: getattr(r, field),
        }
        if context_field:
            row[context_field] = getattr(r, context_field)
        rows.append(row)
    return rows


def batch_data(
    data: list[dict[str, Any]], batch_size: int = 25
) -> list[list[dict[str, Any]]]:
    """Split data into chunks."""
    return [data[i : i + batch_size] for i in range(0, len(data), batch_size)]


def construct_prompt(
    batch: list[dict[str, Any]],
    field: str = "meaning_1",
    context_field: str | None = None,
) -> str:
    """Format the batch into a JSON-like prompt for the given field."""
    batch_json = json.dumps(batch, ensure_ascii=False, indent=2)
    corrected_field = f"{field}_corrected"

    lit_note = ""
    if context_field:
        lit_note = (
            f"IMPORTANT: '{field}' is a deliberately LITERAL gloss of "
            f"'{context_field}' (also shown for context). It is expected to be "
            "non-idiomatic English. Do NOT make it more idiomatic, do NOT rewrite "
            f"it to match '{context_field}', and do NOT change '{context_field}' — "
            "it is context only. Only fix genuine spelling and grammatical typos "
            f"in '{field}'. "
        )

    return (
        f"You are proofreading dictionary '{field}' entries for clear, obvious "
        "spelling mistakes and clear grammatical errors ONLY. Use standard "
        "British English spelling. "
        "If you are unsure whether something is actually wrong, omit that entry "
        "entirely — do not guess. "
        "Do NOT change the meaning, word choice, punctuation style, semicolon "
        "conventions, or abbreviations like (comm). "
        "Do NOT rewrite for style. Do NOT rephrase correct sentences. "
        "Only fix genuine typos and genuine grammatical errors. "
        f"{lit_note}"
        f"Return the result as a JSON list of objects with 'id' and "
        f"'{corrected_field}' fields. "
        "IMPORTANT: Only include entries in the JSON list that actually required "
        "a correction. "
        "DO NOT write any additional notes. "
        "If an entry is already correct, do not include it in the output.\n\n"
        f"{batch_json}"
    )


PRIMARY_PROVIDER = "deepseek"
PRIMARY_MODEL = "deepseek-v4-pro"
FALLBACK_PROVIDER = "zai"
FALLBACK_MODEL = "glm-5.2"


def _parse_corrected_list(response: AIResponse) -> list[dict[str, Any]] | None:
    """Parse a raw AI response into a list of correction dicts, or None on failure."""
    if not response.content:
        pr.red(f"Error: No content from AI: {response.status_message}")
        return None

    try:
        content = response.content.strip()
        # Handle potential markdown formatting
        if content.startswith("```json"):
            content = content.replace("```json", "", 1)
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]

        corrected_list = json.loads(content)
        if isinstance(corrected_list, list):
            return corrected_list
        pr.red(f"Error: AI response is not a list: {response.content}")
        return None
    except json.JSONDecodeError:
        pr.red(f"Error decoding JSON from AI response: {response.content}")
        return None


def process_batch(
    ai_manager: AIManager,
    batch: list[dict[str, Any]],
    field: str = "meaning_1",
    context_field: str | None = None,
) -> tuple[bool, list[dict[str, Any]]]:
    """Send a batch to the AI, trying the primary model then a fallback.

    Returns (success, corrections). success is False only when both models
    failed to return parseable JSON — the caller must not treat that batch as
    checked, so it gets retried on the next run instead of being cached as done.
    """
    prompt = construct_prompt(batch, field, context_field)

    response = ai_manager.request(
        prompt=prompt,
        provider_preference=PRIMARY_PROVIDER,
        model=PRIMARY_MODEL,
    )
    corrected_list = _parse_corrected_list(response)
    if corrected_list is not None:
        return True, corrected_list

    pr.amber(
        f"{PRIMARY_PROVIDER}/{PRIMARY_MODEL} failed, "
        f"retrying with {FALLBACK_PROVIDER}/{FALLBACK_MODEL}."
    )
    response = ai_manager.request(
        prompt=prompt,
        provider_preference=FALLBACK_PROVIDER,
        model=FALLBACK_MODEL,
    )
    corrected_list = _parse_corrected_list(response)
    if corrected_list is not None:
        return True, corrected_list

    return False, []


BATCH_SIZE = 25


def tsv_fieldnames(field: str) -> list[str]:
    """Column order for a field's queue TSV."""
    return ["id", "lemma_1", field, f"{field}_corrected"]


def load_checked_cache(cache_path: Path) -> dict[str, str]:
    """Load the id -> last-checked source-text cache. Missing/broken file -> empty."""
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        pr.red(f"Error loading {cache_path}: {e}")
        return {}


def save_checked_cache(cache_path: Path, cache: dict[str, str]) -> None:
    """Save the id -> last-checked source-text cache.

    Written atomically (temp file + os.replace) — a truncated in-place write,
    if killed mid-write, would make load_checked_cache discard the whole
    cache and force a full re-check, the exact cost this cache exists to avoid.
    """
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_suffix(cache_path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp_path.replace(cache_path)


def load_tsv_queue(tsv_path: Path) -> dict[str, dict[str, str]]:
    """Load the pending-correction queue from the TSV, keyed by id."""
    if not tsv_path.exists():
        return {}
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return {row["id"]: row for row in reader if row.get("id") and row["id"] != "id"}


def save_tsv_queue(
    tsv_path: Path, queue: dict[str, dict[str, str]], field: str = "meaning_1"
) -> None:
    """Write the pending-correction queue back out, sorted by id.

    Written atomically (temp file + os.replace) — a truncated in-place write
    could silently drop corrections the user hasn't yet pulled through PRead.
    """
    tsv_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = tsv_path.with_suffix(tsv_path.suffix + ".tmp")
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=tsv_fieldnames(field), delimiter="\t")
        writer.writeheader()
        for id_str in sorted(queue, key=int):
            writer.writerow(queue[id_str])
    tmp_path.replace(tsv_path)


def filter_unchecked(
    data: list[dict[str, Any]], checked_cache: dict[str, str], field: str = "meaning_1"
) -> list[dict[str, Any]]:
    """Keep only entries whose source text has no cache entry or has changed."""
    return [d for d in data if checked_cache.get(str(d["id"])) != d[field]]


def tsv_lock(tsv_path: Path) -> FileLock:
    """A cross-process lock guarding a proofreader queue TSV.

    The CLI run and gui2's PRead both write these files. A lock alone only
    serializes access — callers must also reload the queue from disk *while
    holding the lock*, right before mutating it, rather than trusting an
    in-memory copy, or a lost-update race (last writer wins) is still possible.
    """
    return FileLock(str(tsv_path) + ".lock")


def build_corrected_by_id(
    corrected_batch: list[dict[str, Any]], field: str = "meaning_1"
) -> dict[str, str]:
    """Index a batch's corrections by id, normalized to str.

    The model may echo "id" back as a string rather than the int we sent;
    normalizing here (rather than at each lookup site) keeps the match
    working regardless of what type the model returns it as.
    """
    corrected_field = f"{field}_corrected"
    return {
        str(item.get("id")): item.get(corrected_field, "") for item in corrected_batch
    }


def apply_checked_item(
    tsv_queue: dict[str, dict[str, str]],
    checked_cache: dict[str, str],
    item: dict[str, Any],
    corrected_meaning: str,
    field: str = "meaning_1",
) -> None:
    """Merge one freshly-checked item into the TSV queue and cache, in place.

    Drops any stale queued row for this id (it referred to now-superseded
    text), adds a fresh row only if a correction was actually found, and
    marks the id as checked against its current source text.
    """
    item_id = str(item["id"])
    tsv_queue.pop(item_id, None)
    if corrected_meaning and corrected_meaning != item[field]:
        row = {
            "id": item_id,
            "lemma_1": item["lemma_1"],
            field: item[field],
            f"{field}_corrected": corrected_meaning,
        }
        tsv_queue[item_id] = row
    checked_cache[item_id] = item[field]


def run_field(
    ai_manager: AIManager,
    db_session: Session,
    field_cfg: ProofreadField,
) -> None:
    """Run one proofreading pass for a single field."""
    field = field_cfg.name
    pr.green_title(f"Proofreading {field}")

    data = get_db_data(
        db_session,
        field=field,
        context_field=field_cfg.context_field,
        only_empty_meaning_1=field_cfg.only_empty_meaning_1,
    )
    pr.green(f"Extracted {len(data)} {field} entries from database.")

    checked_cache = load_checked_cache(field_cfg.cache_path)
    unchecked_data = filter_unchecked(data, checked_cache, field)
    pr.green(
        f"{len(unchecked_data)}/{len(data)} {field} entries need checking "
        f"({len(data) - len(unchecked_data)} unchanged since last check)."
    )

    batches = batch_data(unchecked_data, BATCH_SIZE)

    for i, batch in enumerate(batches):
        pr.green(f"Processing {field} batch {i + 1}/{len(batches)}...")
        success, corrected_batch = process_batch(
            ai_manager, batch, field, field_cfg.context_field
        )

        if not success:
            pr.red(
                f"Batch {i + 1} failed on both models; "
                "leaving these entries unchecked for the next run."
            )
            continue

        corrected_by_id = build_corrected_by_id(corrected_batch, field)

        # Reload fresh under the lock rather than trusting an in-memory
        # copy — gui2's PRead may have popped/saved rows since our last read.
        with tsv_lock(field_cfg.tsv_path):
            tsv_queue = load_tsv_queue(field_cfg.tsv_path)

            for item in batch:
                corrected_meaning = corrected_by_id.get(str(item["id"]), "")
                apply_checked_item(
                    tsv_queue, checked_cache, item, corrected_meaning, field
                )

            save_tsv_queue(field_cfg.tsv_path, tsv_queue, field)

        save_checked_cache(field_cfg.cache_path, checked_cache)
        done = len(checked_cache)
        total = len(data)
        pr.green(
            f"{field} batch: {i + 1}  Done: {done:,}  "
            f"Remaining: {total - done:,}  Total: {total:,}"
        )

    pr.green(f"{field} complete. Results in {field_cfg.tsv_path}")


def build_field_configs(pth: ProjectPaths) -> list[ProofreadField]:
    """The three proofreading passes, in priority order."""
    return [
        ProofreadField(
            name="meaning_1",
            tsv_path=pth.proofreader_tsv_path,
            cache_path=pth.proofreader_checked_json_path,
        ),
        ProofreadField(
            name="meaning_lit",
            tsv_path=pth.proofreader_meaning_lit_tsv_path,
            cache_path=pth.proofreader_meaning_lit_checked_json_path,
            context_field="meaning_1",
        ),
        ProofreadField(
            name="meaning_2",
            tsv_path=pth.proofreader_meaning_2_tsv_path,
            cache_path=pth.proofreader_meaning_2_checked_json_path,
            only_empty_meaning_1=True,
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--field",
        choices=["meaning_1", "meaning_lit", "meaning_2"],
        help="Run only this field's pass (default: run all three).",
    )
    args = parser.parse_args()

    pth = ProjectPaths()
    configs = build_field_configs(pth)
    if args.field:
        configs = [c for c in configs if c.name == args.field]

    db_session = get_db_session(pth.dpd_db_path)
    ai_manager = AIManager()

    try:
        for field_cfg in configs:
            run_field(ai_manager, db_session, field_cfg)
    except Exception as e:  # noqa: BLE001
        pr.red(f"Error during processing: {e}")
    finally:
        db_session.close()

    pr.green("All processing complete.")


class ProofreaderManager:
    """Drains the per-field correction queues for gui2's PRead button.

    Constructed with an ordered list of (field, tsv_path); get_next_correction
    pops from the first non-empty queue and reports which field the row targets
    so the gui can load it into the right add-field.
    """

    def __init__(self, queues: list[tuple[str, str | Path]]):
        self.queues: list[tuple[str, Path]] = [(f, Path(p)) for f, p in queues]

    @property
    def count(self) -> int:
        return sum(len(load_tsv_queue(path)) for _, path in self.queues)

    def get_next_correction(
        self,
    ) -> tuple[dict[str, str] | None, int, str | None]:
        """Retrieve and remove the next correction across all queues.

        Returns (correction, remaining_total, field). Each queue is reloaded
        fresh under its own lock rather than trusting an in-memory copy, which
        may be stale by the time this is called (the CLI writes the same files).
        """
        popped: dict[str, str] | None = None
        popped_field: str | None = None

        for field, path in self.queues:
            with tsv_lock(path):
                queue = load_tsv_queue(path)
                if not queue:
                    continue
                first_id = next(iter(queue))
                popped = queue.pop(first_id)
                popped_field = field
                save_tsv_queue(path, queue, field)
                break

        return popped, self.count, popped_field


if __name__ == "__main__":
    main()
