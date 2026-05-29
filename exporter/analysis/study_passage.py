"""Interactive Pāḷi passage analyzer: retrieve a passage by sutta code, analyze with AI, write a markdown study report."""

import json
import re
from pathlib import Path

from db.db_helpers import get_db_session
from exporter.analysis.paths import ensure_analysis_dirs
from exporter.analysis.passage_extraction import format_extraction_report
from exporter.analysis.translate_core import (
    generate_markdown_report,
    translate_sentence,
)
from tools.ai_manager import AIManager
from exporter.analysis.passage_by_code import PassageResult, get_passage_by_code
from tools.paths import ProjectPaths
from tools.printer import printer as pr


_ANALYSIS_DIRS = ensure_analysis_dirs()
_INPUT_DIR = _ANALYSIS_DIRS.input_dir
_REPORTS_DIR = _ANALYSIS_DIRS.reports_dir
_OUTPUT_DIR = _ANALYSIS_DIRS.output_dir


def _format_selection_preview(result: PassageResult) -> str:
    """Return the same extraction preview used by the extraction-only CLI."""
    return format_extraction_report(result)


def _parse_selection_indices(raw: str, count: int) -> list[int] | None:
    """Parse single numbers, inclusive ranges, and mixed whitespace/comma forms."""
    indices: list[int] = []
    seen: set[int] = set()
    tokens = [token for token in re.split(r"[\s,]+", raw.strip()) if token]
    if not tokens:
        return None

    for token in tokens:
        if "-" in token:
            start_text, sep, end_text = token.partition("-")
            if not sep or not start_text.isdigit() or not end_text.isdigit():
                return None
            start = int(start_text)
            end = int(end_text)
            if start > end or start < 1 or end > count:
                return None
            values = range(start, end + 1)
        else:
            if not token.isdigit():
                return None
            value = int(token)
            if value < 1 or value > count:
                return None
            values = [value]

        for value in values:
            index = value - 1
            if index not in seen:
                seen.add(index)
                indices.append(index)

    return indices


def _select_passage(result: PassageResult) -> tuple[str, str]:
    """Prompt user to select one item or all; returns (text, source_suffix)."""
    unit = "verses" if result.is_verse else "paragraphs"
    singular = "verse" if result.is_verse else "paragraph"
    char = "v" if result.is_verse else "p"
    sep = "\n\n" if result.is_verse else "\n"
    n = len(result.paragraphs)
    word_count = sum(len(p.split()) for p in result.paragraphs)
    pr.green(_format_selection_preview(result))
    pr.green("")
    pr.green(f"{result.source} has {n} {unit} (~{word_count} words).")
    raw = input(
        f"Enter {singular} numbers/ranges (e.g. 1, 1-3, 1 3), or press Enter"
        f" to analyze ALL (⚠ high AI cost/time): "
    ).strip()
    if raw == "":
        return sep.join(result.paragraphs), ""
    indices = _parse_selection_indices(raw, n)
    if indices:
        selected = [result.paragraphs[index] for index in indices]
        suffix_numbers = "-".join(str(index + 1) for index in indices)
        return sep.join(selected), f"_{char}{suffix_numbers}"
    pr.amber(f"Invalid input {raw!r}; analyzing all {n} {unit}.")
    return sep.join(result.paragraphs), ""


def _file_mode() -> tuple[str, str]:
    """Pick a .txt file from the input directory; returns (text, source_stem)."""
    txt_files = sorted(_INPUT_DIR.glob("*.txt"))
    if not txt_files:
        pr.red(f"No .txt files found in {_INPUT_DIR}/")
        raise SystemExit(1)
    pr.green("Available text files:")
    for i, f in enumerate(txt_files, 1):
        pr.green(f"  {i}. {f.name}")
    name = input("Enter filename or number: ").strip()
    chosen: Path | None = None
    if name.isdigit():
        k = int(name)
        if 1 <= k <= len(txt_files):
            chosen = txt_files[k - 1]
        else:
            pr.red(f"Invalid number: {k}")
            raise SystemExit(1)
    else:
        candidate = _INPUT_DIR / name
        if not candidate.exists():
            candidate = _INPUT_DIR / (name + ".txt")
        if candidate.exists():
            chosen = candidate
    if chosen is None:
        pr.red(f"File not found: {name!r}")
        raise SystemExit(1)
    return chosen.read_text(encoding="utf-8").strip(), chosen.stem


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


def main() -> None:
    paths = ProjectPaths()
    if not paths.dpd_db_path.exists():
        pr.red(f"Database not found: {paths.dpd_db_path}")
        raise SystemExit(1)

    pr.green("=" * 50)
    pr.green("Pāḷi Passage Analyzer — Stage 1")
    pr.green("=" * 50)

    raw_code = input(
        "\nEnter a sutta/gāthā code (e.g. DHP12, UD12, ITI37, TH134, SNP3, SN12.3, AN3.12),\n"
        "or press Enter to analyze a text file: "
    ).strip()

    speech_mark_options: dict[str, list[str]] | None = None

    if raw_code:
        pr.cyan_tmr("Retrieving passage")
        try:
            result: PassageResult = get_passage_by_code(raw_code)
        except ValueError as exc:
            pr.no(f"{exc}")
            raise SystemExit(1)
        pr.yes("ok")

        source = result.source
        paragraphs = result.paragraphs
        if len(paragraphs) > 1:
            passage, suffix = _select_passage(result)
            source = source + suffix
        else:
            passage = paragraphs[0]

    else:
        passage, source = _file_mode()

    db_session = get_db_session(paths.dpd_db_path)
    ai_manager = AIManager()
    ai_debug: dict = {}

    try:
        merged = translate_sentence(
            passage,
            db_session,
            ai_manager,
            verse_source=source,
            speech_mark_options=speech_mark_options,
            progress=lambda event: _print_translation_progress(source, event),
            debug=ai_debug,
        )
    finally:
        db_session.close()

    report = generate_markdown_report(merged, passage, verse_id=source)
    report_path = _REPORTS_DIR / f"{source}_study.md"
    report_path.write_text(report, encoding="utf-8")

    json_path = _OUTPUT_DIR / f"{source}_study.json"
    json_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    debug_path = _OUTPUT_DIR / f"{source}_ai_debug.json"
    debug_path.write_text(
        json.dumps(ai_debug, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    pr.green("")
    pr.green(f"Report: {report_path}")
    pr.green("Next steps:")
    pr.green("  1. Open the report, delete unwanted rows, fix wrong IDs in column 1.")
    pr.green("  2. Run: uv run python exporter/analysis/export_words_csv.py")


if __name__ == "__main__":
    main()
