"""Interactive Pāḷi passage analyzer: retrieve a passage by sutta code, analyze with AI, write a markdown study report."""

import argparse
import json
import re
from pathlib import Path
from typing import Any

from db.db_helpers import get_db_session
from exporter.analysis.passage_by_code import PassageResult, get_passage_by_code
from exporter.analysis.paths import ensure_analysis_dirs
from exporter.analysis.translate_core import (
    generate_markdown_report,
    translate_sentence,
)
from tools.ai_manager import AIManager
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from exporter.analysis.ui_utils import (
    _print_translation_progress,
    _write_ai_debug_artifacts,
)

_SELECTION_PREVIEW_WORD_LIMIT = 12


def _format_selection_preview(result: PassageResult) -> str:
    """Format compact passage units for interactive selection."""
    unit = "verse" if result.is_verse else "paragraph"
    plural_unit = unit if len(result.paragraphs) == 1 else f"{unit}s"
    lines = [
        f"Source: {result.source}",
        f"Vagga/Sutta: {result.vagga}",
        f"Units: {len(result.paragraphs)} {plural_unit}",
        "",
    ]

    for index, paragraph in enumerate(result.paragraphs, 1):
        words = paragraph.split()
        preview = " ".join(words[:_SELECTION_PREVIEW_WORD_LIMIT])
        if len(words) > _SELECTION_PREVIEW_WORD_LIMIT:
            preview = f"{preview}…"
        lines.append(f"## {unit.title()} {index} ({len(words)} words): {preview}")

    return "\n".join(lines).rstrip()


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


def _file_mode(input_dir: Path) -> tuple[str, str]:
    """Pick a .txt file from the input directory; returns (text, source_stem)."""
    txt_files = sorted(input_dir.glob("*.txt"))
    if not txt_files:
        pr.red(f"No .txt files found in {input_dir}/")
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
        candidate = input_dir / name
        if not candidate.exists():
            candidate = input_dir / (name + ".txt")
        if candidate.exists():
            chosen = candidate
    if chosen is None:
        pr.red(f"File not found: {name!r}")
        raise SystemExit(1)
    return chosen.read_text(encoding="utf-8").strip(), chosen.stem


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pāḷi passage analyzer — Stage 1")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print raw AI responses and parse errors to the terminal",
    )
    parser.add_argument(
        "--provider",
        help="Force one AI provider for every request (requires --model), e.g. antigravity_cli",
    )
    parser.add_argument(
        "--model",
        help='Force one model for every request (requires --provider), e.g. "GPT-OSS 120B (Medium)"',
    )
    args = parser.parse_args(argv)
    if bool(args.provider) != bool(args.model):
        parser.error("--provider and --model must be used together")
    return args


def main() -> None:
    args = _parse_args()

    paths = ProjectPaths()
    if not paths.dpd_db_path.exists():
        pr.red(f"Database not found: {paths.dpd_db_path}")
        raise SystemExit(1)

    dirs = ensure_analysis_dirs()

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
        passage, source = _file_mode(dirs.input_dir)

    db_session = get_db_session(paths.dpd_db_path)
    ai_manager = AIManager()
    ai_debug: dict[str, Any] = {}

    try:
        merged = translate_sentence(
            passage,
            db_session,
            ai_manager,
            model=args.model,
            provider=args.provider,
            verse_source=source,
            speech_mark_options=speech_mark_options,
            progress=lambda event: _print_translation_progress(source, event),
            debug=ai_debug,
            verbose=args.debug,
        )
    except Exception:
        if args.debug or ai_debug:
            _write_ai_debug_artifacts(
                source, ai_debug, args.debug, dirs.output_dir, dirs.reports_dir
            )
        raise
    finally:
        db_session.close()

    report = generate_markdown_report(merged, passage, verse_id=source)
    report_path = dirs.reports_dir / f"{source}_study.md"
    report_path.write_text(report, encoding="utf-8")

    json_path = dirs.output_dir / f"{source}_study.json"
    json_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_ai_debug_artifacts(
        source, ai_debug, args.debug, dirs.output_dir, dirs.reports_dir
    )

    pr.green("")
    pr.green(f"Report: {report_path}")
    pr.green("Next steps:")
    pr.green("  1. Open the report, delete unwanted rows, fix wrong IDs in column 1.")
    pr.green("  2. Run: uv run python exporter/analysis/export_words_csv.py")


if __name__ == "__main__":
    main()
