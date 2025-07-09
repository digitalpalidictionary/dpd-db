# -*- coding: utf-8 -*-
import configparser
from datetime import date
from typing import Optional

from tools.paths import ProjectPaths
from tools.printer import printer as pr


class UposathaManger:
    """Manage uposatha days."""

    UPOSATHA_DATES = [
        date(2023, 1, 6),
        date(2023, 2, 5),
        date(2023, 3, 6),
        date(2023, 4, 5),
        date(2023, 5, 4),
        date(2023, 6, 3),
        date(2023, 7, 2),
        date(2023, 8, 1),
        date(2023, 8, 31),
        date(2023, 9, 29),
        date(2023, 10, 29),
        date(2023, 11, 27),
        date(2023, 12, 27),
        date(2024, 1, 26),
        date(2024, 2, 24),
        date(2024, 3, 24),
        date(2024, 4, 23),
        date(2024, 5, 22),
        date(2024, 6, 21),
        date(2024, 7, 20),
        date(2024, 8, 19),
        date(2024, 9, 17),
        date(2024, 10, 17),
        date(2024, 11, 15),
        date(2024, 12, 15),
        date(2025, 1, 13),
        date(2025, 2, 12),
        date(2025, 3, 14),
        date(2025, 4, 13),
        date(2025, 5, 12),
        date(2025, 6, 11),
        date(2025, 7, 9),
        date(2025, 7, 10),
        date(2025, 8, 9),
        date(2025, 9, 7),
        date(2025, 10, 7),
        date(2025, 11, 5),
        date(2025, 12, 5),
    ]

    @classmethod
    def _get_config(cls):
        """Lazily load and cache the config."""
        if not hasattr(cls, "_config"):
            cls._config = configparser.ConfigParser()
            cls._config.read(ProjectPaths().uposatha_day_ini)
        return cls._config

    @classmethod
    def uposatha_today(cls) -> bool:
        """Check if today is an uposatha day."""
        return date.today() in cls.UPOSATHA_DATES

    @classmethod
    def read_uposatha_count(cls) -> Optional[str]:
        """Get current uposatha count."""
        try:
            return cls._get_config().get("uposatha", "count")
        except Exception:
            return None

    @classmethod
    def write_uposatha_count(cls, count: int) -> bool:
        """Set uposatha count."""
        try:
            pr.green("updating uposatha count")
            config = cls._get_config()
            config["uposatha"] = {"count": str(count)}
            with open(ProjectPaths().uposatha_day_ini, "w") as f:
                config.write(f)
            pr.yes(count)
            return True
        except Exception:
            return False


if __name__ == "__main__":
    exit(0 if UposathaManger.uposatha_today() else 1)
