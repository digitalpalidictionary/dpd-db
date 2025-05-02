from dataclasses import dataclass
from pathlib import Path


@dataclass
class Gui2Paths:
    gui2_dir: Path = Path("gui2/")
    gui2_data_path: Path = gui2_dir / "data"  # Base data directory

    # Static file paths
    daily_log_path: Path = gui2_data_path / "daily_log.json"
    pass2_auto_json_path: Path = gui2_data_path / "pass2_auto.json"
    pass2_auto_failures_path: Path = gui2_data_path / "pass2_auto_failures.txt"
    history_json_path: Path = gui2_data_path / "history.json"  # Add history path

    # Other paths
    find_words_dump_path: Path = gui2_dir / "find_words_with_examples_dump.json"
    find_words_exceptions_path: Path = gui2_dir / "find_words_with_examples_no.json"
