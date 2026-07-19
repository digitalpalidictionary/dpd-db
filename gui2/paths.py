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
            # Per-user session-state files: concurrent gui2 web instances each
            # write these, and non-atomic JSON writes to a shared file corrupt
            # it. Route them per-user (desktop / primary user "1" is unaffected).
            paths.daily_log_path = data / f"daily_log_{username}.json"
            paths.history_json_path = data / f"history_{username}.json"
            paths.filter_presets_path = data / f"filter_presets_{username}.json"
            # Pass2 stash slots are single-word scratch, written by _click_stash
            # / the commentary + example stash managers. Shared across instances
            # they'd clobber each other, so route per-user too.
            paths.headword_stash_json_path = data / f"headword_stash_{username}.json"
            paths.example_stash_json_path = data / f"example_stash_{username}.json"
            paths.commentary_stash_json_path = (
                data / f"commentary_stash_{username}.json"
            )
        return paths
