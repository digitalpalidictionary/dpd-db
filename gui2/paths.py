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
    pass2_exceptions_path: Path = gui2_data_path / "pass2_exceptions.json"
    pass2_new_words_path: Path = gui2_data_path / "pass2_new_words.json"
    history_json_path: Path = gui2_data_path / "history.json"
    example_stash_json_path: Path = gui2_data_path / "example_stash.json"
    headword_stash_json_path: Path = gui2_data_path / "headword_stash.json"
    corrections_path: Path = gui2_data_path / "corrections.json"
    corrections_added_path: Path = gui2_data_path / "corrections_added.json"
    additions_path: Path = gui2_data_path / "additions.json"
    additions_added_path: Path = gui2_data_path / "additions_added.json"
    filter_presets_path: Path = gui2_data_path / "filter_presets.json"

    # Other paths
    find_words_dump_path: Path = gui2_dir / "data/find_words_with_examples_dump.json"
    find_words_exceptions_path: Path = (
        gui2_dir / "data/find_words_with_examples_no.json"
    )

    @staticmethod
    def for_user(username: str) -> "Gui2Paths":
        """Create paths with username-specific data files for contributors."""
        paths = Gui2Paths()
        if username and username != "1":
            data = paths.gui2_data_path
            paths.additions_path = data / f"additions_{username}.json"
            paths.additions_added_path = data / f"additions_added_{username}.json"
            paths.corrections_path = data / f"corrections_{username}.json"
            paths.corrections_added_path = data / f"corrections_added_{username}.json"
        return paths
