"""Shared runtime paths for the Pali passage analysis exporter."""

from dataclasses import dataclass
from pathlib import Path


ANALYSIS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class AnalysisDirs:
    """Runtime directories used by the passage analysis pipeline."""

    root: Path
    input_dir: Path
    reports_dir: Path
    output_dir: Path


def ensure_analysis_dirs(root: Path = ANALYSIS_DIR) -> AnalysisDirs:
    """Create and return the analysis input, reports, and output directories."""
    input_dir = root / "input"
    reports_dir = root / "reports"
    output_dir = root / "output"

    for directory in (input_dir, reports_dir, output_dir):
        directory.mkdir(parents=True, exist_ok=True)

    return AnalysisDirs(
        root=root,
        input_dir=input_dir,
        reports_dir=reports_dir,
        output_dir=output_dir,
    )
