import json
from pathlib import Path
from typing import Any
from tools.printer import printer as pr


def _print_translation_progress(source: str, event: str) -> None:
    """Print timed progress for local JSON analysis and AI analysis stages."""
    if event == "json_start":
        pr.green_tmr("Building analysis JSON")
    elif event == "json_done":
        pr.yes("done")
    elif event == "ai_start":
        pr.green_tmr(f"Analyzing {source!r}")
    elif event == "ai_done":
        pr.yes("done")
    elif event == "ai_reformat_start":
        pr.green_tmr("Reformatting non-standard response")
    elif event == "ai_reformat_done":
        pr.yes("done")
    elif event == "ai_translation_start":
        pr.green_tmr("Fetching translation for word→key map")
    elif event == "ai_translation_done":
        pr.yes("done")


def _build_raw_responses_log(source: str, ai_debug: dict[str, Any]) -> str:
    """Collect all raw AI responses from a debug dict into one readable text file."""
    sections: list[str] = [f"# Raw AI responses for {source}\n"]

    def _section(title: str, status: str, content: str | None) -> str:
        body = content if content else "(no content)"
        return f"## {title}\nStatus: {status}\n\n{body}\n"

    if "raw_response" in ai_debug:
        sections.append(
            _section(
                "First response",
                ai_debug.get("status_message", ""),
                ai_debug.get("raw_response"),
            )
        )

    if "reformat_raw_response" in ai_debug:
        sections.append(
            _section(
                "Reformat response",
                ai_debug.get("reformat_status_message", ""),
                ai_debug.get("reformat_raw_response"),
            )
        )

    if "translation_raw_response" in ai_debug:
        sections.append(
            _section(
                "Translation response (word→key map path)",
                ai_debug.get("translation_status_message", ""),
                ai_debug.get("translation_raw_response"),
            )
        )

    for i, chunk in enumerate(ai_debug.get("chunk_requests", []), start=1):
        sections.append(
            _section(
                f"Chunk {i} first response",
                chunk.get("status_message", ""),
                chunk.get("raw_response"),
            )
        )
        if "reformat_raw_response" in chunk:
            sections.append(
                _section(
                    f"Chunk {i} reformat response",
                    chunk.get("reformat_status_message", ""),
                    chunk.get("reformat_raw_response"),
                )
            )
        if "translation_raw_response" in chunk:
            sections.append(
                _section(
                    f"Chunk {i} translation response (word→key map path)",
                    chunk.get("translation_status_message", ""),
                    chunk.get("translation_raw_response"),
                )
            )

    for i, retry in enumerate(ai_debug.get("retry_requests", []), start=1):
        sections.append(
            _section(
                f"Retry {i} (missing scores)",
                retry.get("status_message", ""),
                retry.get("raw_response"),
            )
        )

    return "\n".join(sections)


def _write_ai_debug_artifacts(
    source: str,
    ai_debug: dict[str, Any],
    include_raw: bool,
    output_dir: Path,
    reports_dir: Path,
) -> None:
    """Write AI debug JSON and optionally the readable raw-response log."""
    debug_path = output_dir / f"{source}_ai_debug.json"
    debug_path.write_text(
        json.dumps(ai_debug, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if include_raw:
        raw_path = reports_dir / f"{source}_ai_raw.txt"
        raw_path.write_text(
            _build_raw_responses_log(source, ai_debug),
            encoding="utf-8",
        )
        pr.green(f"Raw AI responses: {raw_path}")
