"""AI-Powered Dictionary Proofreading System."""

import csv
import json
from typing import Any
from pathlib import Path
from sqlalchemy.orm import Session
from db.models import DpdHeadword
from db.db_helpers import get_db_session
from tools.ai_manager import AIManager
from tools.printer import printer as pr


def get_db_data(db_session: Session) -> list[dict[str, Any]]:
    """Query DpdHeadword table for entries with meanings."""
    results = db_session.query(DpdHeadword).filter(DpdHeadword.meaning_1 != "").all()
    return [
        {"id": r.id, "lemma_1": r.lemma_1, "meaning_1": r.meaning_1} for r in results
    ]


def batch_data(
    data: list[dict[str, Any]], batch_size: int = 50
) -> list[list[dict[str, Any]]]:
    """Split data into chunks."""
    return [data[i : i + batch_size] for i in range(0, len(data), batch_size)]


def construct_prompt(batch: list[dict[str, Any]]) -> str:
    """Format the batch into a JSON-like prompt."""
    batch_json = json.dumps(batch, ensure_ascii=False, indent=2)
    return (
        "Correct the spelling and grammar of the following dictionary meanings. "
        "Correct all spelling mistakes, and only serious grammatical errors. "
        "Phrases starting with 'who ...' are ok, unless there's another problem. "
        "Separate meanings with a semicolon. "
        "DO NOT add a fulltop at the end of the meaning. "
        "DO NOT add a fullstop to abbreaviations like (comm). "
        "Use standard British English spelling. "
        "Return the result as a JSON list of objects with 'id' and 'meaning_1_corrected' fields. "
        "IMPORTANT: Only include entries in the JSON list that actually required a correction. "
        "DO NOT write any additional notes. "
        "If a meaning is already correct, do not include it in the output. "
        "Do not change the meaning, only fix errors.\n\n"
        f"{batch_json}"
    )


def process_batch(
    ai_manager: AIManager,
    batch: list[dict[str, Any]],
    model: str,
) -> list[dict[str, Any]]:
    """Send a batch to the AI and parse the response."""
    prompt = construct_prompt(batch)

    # Using AIManager allows for fallback and easy model switching.
    # Specify OpenRouter and the free model as requested.
    response = ai_manager.request(
        prompt=prompt,
        provider_preference="openrouter",
        model=model,
    )

    if response.content:
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
            pr.error(f"Error: AI response is not a list: {response.content}")
        except json.JSONDecodeError:
            pr.error(f"Error decoding JSON from AI response: {response.content}")
    else:
        pr.error(f"Error: No content from AI: {response.status_message}")

    return []


def main():
    batch_size = 100
    output_file = "tools/proofreader.tsv"
    db_path = "dpd.db"
    model = "nvidia/nemotron-3-nano-30b-a3b:free"
    # model = "kwaipilot/kat-coder-pro:free"
    # model = "xiaomi/mimo-v2-flash:free"
    # model = "google/gemini-2.0-flash-exp:free"
    # model = "mistralai/devstral-2512:free"
    # model = "z-ai/glm-4.5-air:free"

    db_session = get_db_session(Path(db_path))
    data = get_db_data(db_session)
    pr.info(f"Extracted {len(data)} entries from database.")

    batches = batch_data(data, batch_size)
    ai_manager = AIManager()

    lookup = {d["id"]: d for d in data}
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        output_exists = output_path.exists()
        with open(output_path, "a", newline="", encoding="utf-8") as tsvfile:
            fieldnames = ["id", "lemma_1", "meaning_1", "meaning_1_corrected"]
            writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter="\t")
            if not output_exists or output_path.stat().st_size == 0:
                writer.writeheader()

            for i, batch in enumerate(batches):
                pr.info(f"Processing batch {i + 1}/{len(batches)}...")
                corrected_batch = process_batch(ai_manager, batch, model)

                batch_results = []

                for item in corrected_batch:
                    item_id = item.get("id")

                    if item_id in lookup:
                        original = lookup[item_id]

                        corrected_meaning = item.get("meaning_1_corrected", "")

                        if (
                            corrected_meaning
                            and corrected_meaning != original["meaning_1"]
                        ):
                            result = original.copy()

                            result["meaning_1_corrected"] = corrected_meaning

                            batch_results.append(result)

                if batch_results:
                    writer.writerows(batch_results)
                    tsvfile.flush()
                    pr.info(f"Batch {i + 1} results written to {output_file}")

    except Exception as e:
        pr.error(f"Error during processing: {e}")
    finally:
        db_session.close()

    pr.info(f"All processing complete. Results saved in {output_file}")


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
        except Exception as e:
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
        except Exception as e:
            print(f"Error saving {self.tsv_path}: {e}")

    @property
    def count(self) -> int:
        return len(self.corrections)

    def get_next_correction(self) -> tuple[dict[str, str] | None, int]:
        """
        Retrieves and removes the next correction from the list.
        Returns a tuple of (correction, remaining_count).
        """
        self.corrections = self.load_corrections()
        if not self.corrections:
            return None, 0

        correction = self.corrections.pop(0)
        self.save_corrections()
        return correction, len(self.corrections)


if __name__ == "__main__":
    main()
