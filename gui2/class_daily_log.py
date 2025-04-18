import datetime
import json
from math import e
from pathlib import Path


class DailyLog:
    """Daily log counter"""

    def __init__(self) -> None:
        self.file_path: Path = Path("gui2/data/daily_log.json")
        self.data: dict[str, dict[str, int]] = self._load()

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
        """Increments 'pass1' or 'pass2' for today and saves."""
        if key not in ["pass1", "pass2"]:
            raise ValueError("Key must be 'pass1' or 'pass2'")
        today_str = datetime.date.today().isoformat()
        today_entry = self.data.setdefault(today_str, {"pass1": 0, "pass2": 0})
        today_entry[key] = today_entry.get(key, 0) + count
        self._save()
        return self.get_counts()

    def get_counts(self) -> str:
        """Gets today's counts (pass1, pass2)."""
        today_str = datetime.date.today().isoformat()
        today_entry = self.data.get(today_str, {"pass1": 0, "pass2": 0})
        # return (today_entry.get("pass1", 0), today_entry.get("pass2", 0))
        return f"pass1: {today_entry.get('pass1', 0)}. pass2: {today_entry.get('pass2', 0)}  "

    def get_history(self) -> dict[str, dict[str, int]]:
        """Returns the entire history data."""
        return self.data


# log = DailyLog()
# log.increment("pass1")  # Add 5 to pass1
# log.increment("pass2")  # Add 1 to pass2
# print(log.get_counts())  # View today's counts
# print(log.get_history())  # View all historical data
