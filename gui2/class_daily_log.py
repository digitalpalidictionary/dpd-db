import datetime
import json
from pathlib import Path

from gui2.class_appbar_updater import AppBarUpdater
from gui2.class_paths import Gui2Paths


class DailyLog:
    """Daily log counter"""

    def __init__(self, appbar_updater: AppBarUpdater) -> None:
        self.gui2pth = Gui2Paths()
        self.file_path: Path = self.gui2pth.daily_log_path
        self.data: dict[str, dict[str, int]] = self._load()
        self.appbar_updater = appbar_updater

    def _load(self) -> dict[str, dict[str, int]]:
        """Loads data, assumes file exists and is valid."""
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save(self) -> None:
        """Saves data, assumes success."""
        with open(self.file_path, "w") as f:
            json.dump(self.data, f, indent=4, sort_keys=True)

    def increment(self, key: str, count: int = 1) -> str:
        """Increments 'pass1', 'pass2' or 'pass2_pre' for today and saves."""
        if key not in ["pass1", "pass2", "pass2_pre"]:
            raise ValueError("Key must be 'pass1', 'pass2' or 'pass2_pre'")
        today_str = datetime.date.today().isoformat()
        today_entry = self.data.setdefault(
            today_str, {"pass1": 0, "pass2": 0, "pass2_pre": 0}
        )
        today_entry[key] = today_entry.get(key, 0) + count
        self._save()
        return self.get_counts()

    def get_counts(self) -> str:
        """Gets today's counts (pass1, pass2)."""
        today_str = datetime.date.today().isoformat()
        today_entry = self.data.get(today_str, {"pass1": 0, "pass2": 0, "pass2_pre": 0})
        # return (today_entry.get("pass1", 0), today_entry.get("pass2", 0))
        return f"pass1: {today_entry.get('pass1', 0)} pass2_pre: {today_entry.get('pass2_pre', 0)} pass2: {today_entry.get('pass2', 0)}  "

    def get_history(self) -> dict[str, dict[str, int]]:
        """Returns the entire history data."""
        return self.data


# log = DailyLog()
# log.increment("pass1")  # Add 5 to pass1
# log.increment("pass2")  # Add 1 to pass2
# print(log.get_counts())  # View today's counts
# print(log.get_history())  # View all historical data
