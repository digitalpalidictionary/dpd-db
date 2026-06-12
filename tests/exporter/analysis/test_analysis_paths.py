"""Verify analysis exporter runtime directories are created on demand."""

from pathlib import Path

from exporter.analysis.paths import ensure_analysis_dirs


def test_ensure_analysis_dirs_creates_required_subdirectories(tmp_path: Path) -> None:
    root = tmp_path / "analysis"

    dirs = ensure_analysis_dirs(root)

    assert dirs.input_dir == root / "input"
    assert dirs.reports_dir == root / "reports"
    assert dirs.output_dir == root / "output"
    assert dirs.input_dir.is_dir()
    assert dirs.reports_dir.is_dir()
    assert dirs.output_dir.is_dir()
