"""Test double that replays recorded AI responses from fixtures."""

import json
from collections import deque
from pathlib import Path
from typing import NamedTuple


class AIResponse(NamedTuple):
    content: str | None
    status_message: str


class RecordedAIManager:
    """Replays AI responses from a *_ai_debug.json fixture in order."""

    def __init__(self, debug_json_path: Path):
        self.responses: deque[tuple[str, AIResponse]] = deque()
        self._load_responses(debug_json_path)
        self.call_count = 0

    def _load_responses(self, path: Path):
        with open(path) as f:
            data = json.load(f)

        # Single-chunk or multi-chunk passages
        chunks = data.get("chunk_requests", [data])
        # If chunk_requests exists but data has its own keys (unlikely in current schema
        # but handled by the dry-replay logic), prioritize chunk_requests.
        if "chunk_requests" not in data and "raw_response" not in data:
            # Possibly an empty or malformed debug file
            return

        for chunk in chunks:
            if "raw_response" in chunk:
                self.responses.append(
                    (
                        "first_pass",
                        AIResponse(
                            chunk["raw_response"], chunk.get("status_message", "")
                        ),
                    )
                )
            if "translation_raw_response" in chunk:
                self.responses.append(
                    (
                        "translation",
                        AIResponse(
                            chunk["translation_raw_response"],
                            chunk.get("translation_status_message", ""),
                        ),
                    )
                )
            if "reformat_raw_response" in chunk:
                self.responses.append(
                    (
                        "reformat",
                        AIResponse(
                            chunk["reformat_raw_response"],
                            chunk.get("reformat_status_message", ""),
                        ),
                    )
                )

        # Retry passes
        for retry in data.get("retry_requests", []):
            self.responses.append(
                (
                    "retry",
                    AIResponse(retry["raw_response"], retry.get("status_message", "")),
                )
            )

    def request(
        self,
        prompt: str,
        prompt_sys: str | None = None,
        provider_preference: str | None = None,
        model: str | None = None,
        grounding: bool = False,
        **kwargs,
    ) -> AIResponse:
        self.call_count += 1

        # Classify the incoming prompt
        if prompt.startswith("Return JSON for:"):
            actual_class = "first_pass"
        elif prompt.startswith("Translate this Pāḷi sentence into English:"):
            actual_class = "translation"
        elif prompt.startswith("Your previous response for the Pāḷi sentence"):
            actual_class = "reformat"
        elif prompt.startswith("Please supply missing dictionary option scores"):
            actual_class = "retry"
        else:
            raise ValueError(
                f"Unknown prompt type at call {self.call_count}: {prompt[:50]}..."
            )

        if not self.responses:
            raise RuntimeError(
                f"RecordedAIManager: Queue overrun at call {self.call_count}. "
                f"Expected a {actual_class} call but no more recorded responses remain."
            )

        expected_class, response = self.responses.popleft()

        if actual_class != expected_class:
            raise RuntimeError(
                f"RecordedAIManager: Desync at call {self.call_count}. "
                f"Pipeline requested {actual_class}, but transcript expected {expected_class}."
            )

        return response

    def assert_empty(self):
        """Assert that all recorded responses were consumed."""
        if self.responses:
            remaining = [c for c, _ in self.responses]
            raise RuntimeError(
                f"RecordedAIManager: {len(self.responses)} responses were not consumed: {remaining}"
            )
