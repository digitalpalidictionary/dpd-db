# -*- coding: utf-8 -*-
import datetime
import json
from pathlib import Path

from gui2.toolkit import ToolKit  # Import ToolKit


class DailyLog:
    """Daily log counter"""

    def __init__(self, toolkit: ToolKit) -> None:
        self.gui2pth = toolkit.paths
        self.file_path: Path = self.gui2pth.daily_log_path
        self.data: dict[str, dict[str, int]] = self._load()
        self.appbar_updater = toolkit.appbar_updater

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

    def increment(self, key: str, count: int = 1) -> None:
        """Increments 'pass1', 'pass2' or 'pass2_pre' for today, saves and updates appbar."""
        valid_keys = ["pass1", "pass2_pre", "pass2_add", "pass2_update"]
        if key not in valid_keys:
            raise ValueError(f"Key must be one of {valid_keys}")
        today_str = datetime.date.today().isoformat()
        today_entry = self.data.setdefault(
            today_str,
            {
                "pass1": 0,
                "pass2_pre": 0,
                "pass2_add": 0,
                "pass2_update": 0,
            },
        )
        today_entry[key] = today_entry.get(key, 0) + count
        self._save()
        self.appbar_updater.update(self.get_counts())

    def get_counts(self) -> str:
        """Gets today's counts (pass1, pass2)."""
        today_str = datetime.date.today().isoformat()
        today_entry = self.data.get(
            today_str,
            {
                "pass1": 0,
                "pass2_pre": 0,
                "pass2_add": 0,
                "pass2_update": 0,
            },
        )
        return (
            f"pass1: {today_entry.get('pass1', 0)} pass2_pre: {today_entry.get('pass2_pre', 0)} "
            f"pass2_add: {today_entry.get('pass2_add', 0)} pass2_update: {today_entry.get('pass2_update', 0)}  "
        )

    def get_history(self) -> dict[str, dict[str, int]]:
        """Returns the entire history data."""
        return self.data


# log = DailyLog()
# log.increment("pass1")  # Add 5 to pass1
# log.increment("pass2")  # Add 1 to pass2
# print(log.get_counts())  # View today's counts
# print(log.get_history())  # View all historical data
