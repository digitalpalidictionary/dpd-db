import os
from pathlib import Path


class Gui2Paths:
    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            base_dir = Path(os.path.abspath("."))

        self.gui2_dir: Path = base_dir / "gui2"
        self.gui2_data_path: Path = self.gui2_dir / "data"  # Base data directory

        # Static file paths
        self.daily_log_path: Path = self.gui2_data_path / "daily_log.json"
        self.pass2_auto_json_path: Path = self.gui2_data_path / "pass2_auto.json"
        self.pass2_auto_failures_path: Path = (
            self.gui2_data_path / "pass2_auto_failures.txt"
        )
        self.pass2_exceptions_path: Path = self.gui2_data_path / "pass2_exceptions.json"
        self.pass2_new_words_path: Path = self.gui2_data_path / "pass2_new_words.json"
        self.pass2_eg_words_path: Path = self.gui2_data_path / "pass2_eg_words.json"
        self.history_json_path: Path = self.gui2_data_path / "history.json"
        self.example_stash_json_path: Path = self.gui2_data_path / "example_stash.json"
        self.commentary_stash_json_path: Path = (
            self.gui2_data_path / "commentary_stash.json"
        )
        self.headword_stash_json_path: Path = (
            self.gui2_data_path / "headword_stash.json"
        )
        self.corrections_path: Path = self.gui2_data_path / "corrections.json"
        self.corrections_added_path: Path = (
            self.gui2_data_path / "corrections_added.json"
        )
        self.additions_path: Path = self.gui2_data_path / "additions.json"
        self.additions_added_path: Path = self.gui2_data_path / "additions_added.json"
        self.filter_presets_path: Path = self.gui2_data_path / "filter_presets.json"
        self.in_commentary_exceptions_path: Path = (
            self.gui2_data_path / "in_commentary_exceptions.txt"
        )

        # Other paths
        self.pass2_x_manager_py_path: Path = self.gui2_dir / "pass2_x_manager.py"
        self.find_words_dump_path: Path = (
            self.gui2_dir / "data/find_words_with_examples_dump.json"
        )
        self.find_words_exceptions_path: Path = (
            self.gui2_dir / "data/find_words_with_examples_no.json"
        )

    @staticmethod
    def for_user(username: str, base_dir: Path | None = None) -> "Gui2Paths":
        """Create paths with username-specific data files for contributors."""
        paths = Gui2Paths(base_dir)
        if username and username != "1":
            data = paths.gui2_data_path
            paths.additions_path = data / f"additions_{username}.json"
            paths.additions_added_path = data / f"additions_added_{username}.json"
            paths.corrections_path = data / f"corrections_{username}.json"
            paths.corrections_added_path = data / f"corrections_added_{username}.json"
        return paths
