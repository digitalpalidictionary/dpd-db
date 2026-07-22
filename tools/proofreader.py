"""AI-Powered Dictionary Proofreading System."""

import csv
import json
from pathlib import Path
from typing import Any

from filelock import FileLock
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.ai_manager import AIManager, AIResponse
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def get_db_data(db_session: Session) -> list[dict[str, Any]]:
    """Query DpdHeadword table for entries with meanings."""
    results = db_session.query(DpdHeadword).filter(DpdHeadword.meaning_1 != "").all()
    return [
        {"id": r.id, "lemma_1": r.lemma_1, "meaning_1": r.meaning_1} for r in results
    ]


def batch_data(
    data: list[dict[str, Any]], batch_size: int = 25
) -> list[list[dict[str, Any]]]:
    """Split data into chunks."""
    return [data[i : i + batch_size] for i in range(0, len(data), batch_size)]


def construct_prompt(batch: list[dict[str, Any]]) -> str:
    """Format the batch into a JSON-like prompt."""
    batch_json = json.dumps(batch, ensure_ascii=False, indent=2)
    return (
        "You are proofreading dictionary meanings for clear, obvious spelling mistakes "
        "and clear grammatical errors ONLY. Use standard British English spelling. "
        "If you are unsure whether something is actually wrong, omit that entry entirely — "
        "do not guess. "
        "Do NOT change the meaning, word choice, punctuation style, semicolon conventions, "
        "or abbreviations like (comm). "
        "Do NOT rewrite for style. Do NOT rephrase correct sentences. "
        "Only fix genuine typos and genuine grammatical errors. "
        "Return the result as a JSON list of objects with 'id' and 'meaning_1_corrected' fields. "
        "IMPORTANT: Only include entries in the JSON list that actually required a correction. "
        "DO NOT write any additional notes. "
        "If a meaning is already correct, do not include it in the output.\n\n"
        f"{batch_json}"
    )


PRIMARY_PROVIDER = "zai"
PRIMARY_MODEL = "glm-5.2"
FALLBACK_PROVIDER = "deepseek"
FALLBACK_MODEL = "deepseek-v4-flash"


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
) -> tuple[bool, list[dict[str, Any]]]:
    """Send a batch to the AI, trying the primary model then a fallback.

    Returns (success, corrections). success is False only when both models
    failed to return parseable JSON — the caller must not treat that batch as
    checked, so it gets retried on the next run instead of being cached as done.
    """
    prompt = construct_prompt(batch)

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
TSV_FIELDNAMES = ["id", "lemma_1", "meaning_1", "meaning_1_corrected"]


def load_checked_cache(cache_path: Path) -> dict[str, str]:
    """Load the id -> last-checked meaning_1 cache. Missing/broken file -> empty."""
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        pr.red(f"Error loading {cache_path}: {e}")
        return {}


def save_checked_cache(cache_path: Path, cache: dict[str, str]) -> None:
    """Save the id -> last-checked meaning_1 cache.

    Written atomically (temp file + os.replace) — a truncated in-place write,
    if killed mid-write, would make load_checked_cache discard the whole
    cache and force a full 63k-row re-check, the exact cost this cache exists
    to avoid.
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


def save_tsv_queue(tsv_path: Path, queue: dict[str, dict[str, str]]) -> None:
    """Write the pending-correction queue back out, sorted by id.

    Written atomically (temp file + os.replace) — a truncated in-place write
    could silently drop corrections the user hasn't yet pulled through PRead.
    """
    tsv_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = tsv_path.with_suffix(tsv_path.suffix + ".tmp")
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_FIELDNAMES, delimiter="\t")
        writer.writeheader()
        for id_str in sorted(queue, key=int):
            writer.writerow(queue[id_str])
    tmp_path.replace(tsv_path)


def filter_unchecked(
    data: list[dict[str, Any]], checked_cache: dict[str, str]
) -> list[dict[str, Any]]:
    """Keep only entries whose meaning_1 has no cache entry or has changed."""
    return [d for d in data if checked_cache.get(str(d["id"])) != d["meaning_1"]]


def tsv_lock(tsv_path: Path) -> FileLock:
    """A cross-process lock guarding tools/proofreader.tsv.

    The CLI run and gui2's PRead both write this file. A lock alone only
    serializes access — callers must also reload the queue from disk *while
    holding the lock*, right before mutating it, rather than trusting an
    in-memory copy, or a lost-update race (last writer wins) is still possible.
    """
    return FileLock(str(tsv_path) + ".lock")


def build_corrected_by_id(corrected_batch: list[dict[str, Any]]) -> dict[str, str]:
    """Index a batch's corrections by id, normalized to str.

    The model may echo "id" back as a string rather than the int we sent;
    normalizing here (rather than at each lookup site) keeps the match
    working regardless of what type the model returns it as.
    """
    return {
        str(item.get("id")): item.get("meaning_1_corrected", "")
        for item in corrected_batch
    }


def apply_checked_item(
    tsv_queue: dict[str, dict[str, str]],
    checked_cache: dict[str, str],
    item: dict[str, Any],
    corrected_meaning: str,
) -> None:
    """Merge one freshly-checked item into the TSV queue and cache, in place.

    Drops any stale queued row for this id (it referred to now-superseded
    text), adds a fresh row only if a correction was actually found, and
    marks the id as checked against its current meaning_1.
    """
    item_id = str(item["id"])
    tsv_queue.pop(item_id, None)
    if corrected_meaning and corrected_meaning != item["meaning_1"]:
        row = item.copy()
        row["meaning_1_corrected"] = corrected_meaning
        tsv_queue[item_id] = row
    checked_cache[item_id] = item["meaning_1"]


def main():
    pth = ProjectPaths()
    output_file = pth.proofreader_tsv_path
    cache_file = pth.proofreader_checked_json_path
    db_path = pth.dpd_db_path

    db_session = get_db_session(db_path)
    data = get_db_data(db_session)
    pr.green(f"Extracted {len(data)} entries from database.")

    checked_cache = load_checked_cache(cache_file)
    unchecked_data = filter_unchecked(data, checked_cache)
    pr.green(
        f"{len(unchecked_data)}/{len(data)} entries need checking "
        f"({len(data) - len(unchecked_data)} unchanged since last check)."
    )

    batches = batch_data(unchecked_data, BATCH_SIZE)
    ai_manager = AIManager()

    try:
        for i, batch in enumerate(batches):
            pr.green(f"Processing batch {i + 1}/{len(batches)}...")
            success, corrected_batch = process_batch(ai_manager, batch)

            if not success:
                pr.red(
                    f"Batch {i + 1} failed on both models; "
                    "leaving these entries unchecked for the next run."
                )
                continue

            corrected_by_id = build_corrected_by_id(corrected_batch)

            # Reload fresh under the lock rather than trusting an in-memory
            # copy — gui2's PRead may have popped/saved rows since our last read.
            with tsv_lock(output_file):
                tsv_queue = load_tsv_queue(output_file)

                for item in batch:
                    corrected_meaning = corrected_by_id.get(str(item["id"]), "")
                    apply_checked_item(
                        tsv_queue, checked_cache, item, corrected_meaning
                    )

                save_tsv_queue(output_file, tsv_queue)

            save_checked_cache(cache_file, checked_cache)
            done = len(checked_cache)
            total = len(data)
            pr.green(
                f"Batch: {i + 1}  Done: {done:,}  "
                f"Remaining: {total - done:,}  Total: {total:,}"
            )

    except Exception as e:  # noqa: BLE001
        pr.red(f"Error during processing: {e}")
    finally:
        db_session.close()

    pr.green(f"All processing complete. Results saved in {output_file}")


class ProofreaderManager:
    def __init__(self, tsv_path: str | Path):
        self.tsv_path = Path(tsv_path)
        self.corrections: list[dict[str, str]] = self.load_corrections()

    def load_corrections(self) -> list[dict[str, str]]:
        if not self.tsv_path.exists():
            return []
        try:
            with open(self.tsv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                # Filter out header rows and empty rows
                return [row for row in reader if row.get("id") and row["id"] != "id"]
        except Exception as e:  # noqa: BLE001
            print(f"Error loading {self.tsv_path}: {e}")
            return []

    def save_corrections(self) -> None:
        try:
            with open(self.tsv_path, "w", newline="", encoding="utf-8") as f:
                if not self.corrections:
                    # Write header even if empty
                    writer = csv.DictWriter(
                        f,
                        fieldnames=[
                            "id",
                            "lemma_1",
                            "meaning_1",
                            "meaning_1_corrected",
                        ],
                        delimiter="\t",
                    )
                    writer.writeheader()
                    return

                fieldnames = list(self.corrections[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
                writer.writeheader()
                writer.writerows(self.corrections)
        except Exception as e:  # noqa: BLE001
            print(f"Error saving {self.tsv_path}: {e}")

    @property
    def count(self) -> int:
        return len(self.corrections)

    def get_next_correction(self) -> tuple[dict[str, str] | None, int]:
        """
        Retrieves and removes the next correction from the list.
        Returns a tuple of (correction, remaining_count).

        Locked against the CLI proofreader run, which writes the same TSV —
        reloads fresh under the lock rather than trusting self.corrections,
        which may be stale by the time this is called.
        """
        with tsv_lock(self.tsv_path):
            self.corrections = self.load_corrections()
            if not self.corrections:
                return None, 0

            correction = self.corrections.pop(0)
            self.save_corrections()
            return correction, len(self.corrections)


if __name__ == "__main__":
    main()
