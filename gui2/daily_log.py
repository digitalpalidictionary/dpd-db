# -*- coding: utf-8 -*-
import datetime
import json
from pathlib import Path

from gui2.toolkit import ToolKit  # Import ToolKit
from tools.printer import printer as pr
from tools.server_mode import is_headless_server


class DailyLog:
    """Daily log counter"""

    def __init__(self, toolkit: ToolKit) -> None:
        self.gui2pth = toolkit.paths
        self.file_path: Path = self.gui2pth.daily_log_path
        self.data: dict[str, dict[str, int]] = self._load()
        self.appbar_updater = toolkit.appbar_updater
        self._pass1_only: bool = is_headless_server()

    def _load(self) -> dict[str, dict[str, int]]:
        """Loads data, assumes file exists and is valid."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            # A write cut off mid-way leaves an empty file. Without this the
            # editor could not start at all until someone repaired it by hand.
            corrupt = self.file_path.with_name(self.file_path.name + ".corrupt")
            self.file_path.replace(corrupt)
            pr.red(f"{self.file_path.name} is damaged, kept as {corrupt.name}")
            return {}

    def _save(self) -> None:
        """Saves data, assumes success."""
        # Write then swap, so a kill mid-write cannot leave a half-written file.
        tmp = self.file_path.with_name(self.file_path.name + ".tmp")
        tmp.write_text(
            json.dumps(self.data, indent=4, sort_keys=True), encoding="utf-8"
        )
        tmp.replace(self.file_path)

    def increment(self, key: str, count: int = 1) -> None:
        """Increments 'pass1', 'pass2' or 'pass2_pre' for today, saves and updates appbar."""
        valid_keys = ["pass1", "pass2_pre", "pass2x", "pass2_add", "pass2_update"]
        if key not in valid_keys:
            raise ValueError(f"Key must be one of {valid_keys}")
        today_str = datetime.date.today().isoformat()
        today_entry = self.data.setdefault(
            today_str,
            {
                "pass1": 0,
                "pass2_pre": 0,
                "pass2x": 0,
                "pass2_add": 0,
                "pass2_update": 0,
            },
        )
        today_entry[key] = today_entry.get(key, 0) + count
        self._save()
        self.appbar_updater.update(self.get_counts())

    def get_count(self, key: str) -> int:
        """Gets today's count for a specific key."""
        today_str = datetime.date.today().isoformat()
        return self.data.get(today_str, {}).get(key, 0)

    def get_counts(self) -> str:
        """Gets today's counts (pass1, pass2)."""
        today_str = datetime.date.today().isoformat()
        today_entry = self.data.get(
            today_str,
            {
                "pass1": 0,
                "pass2_pre": 0,
                "pass2x": 0,
                "pass2_add": 0,
                "pass2_update": 0,
            },
        )
        # A contributor can only use Pass1Add, so the other counters stay at 0.
        if self._pass1_only:
            return f"pass1: {today_entry.get('pass1', 0)}  "
        return (
            f"pass1: {today_entry.get('pass1', 0)} pass2_pre: {today_entry.get('pass2_pre', 0)} "
            f"pass2x: {today_entry.get('pass2x', 0)} "
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
