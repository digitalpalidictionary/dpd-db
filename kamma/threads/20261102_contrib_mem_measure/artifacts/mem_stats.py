"""Median, spread and delta helpers shared by mem_probe.py and make_tables.py."""

import json
import statistics
from pathlib import Path
from typing import Any

SPREAD_LIMIT = 0.10
WHOLE_RUN_POINTS = {"staircase", "books_cumulative"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def median(values: list[float]) -> float:
    return statistics.median(values)


def spread_flag(values: list[float]) -> bool:
    """True when (max - min) is more than 10 % of the median."""
    if len(values) < 2:
        return False
    mid = median(values)
    if mid <= 0:
        return False
    return (max(values) - min(values)) > SPREAD_LIMIT * mid


def summarize(values: list[float]) -> dict[str, Any]:
    return {
        "n": len(values),
        "median": median(values),
        "min": min(values),
        "max": max(values),
        "flag": spread_flag(values),
    }


def partial_status(outcomes: list[str]) -> str:
    """`ok` when every run is ok, `failed` when none is, else `partial`."""
    ok = sum(1 for o in outcomes if o == "ok")
    if ok == len(outcomes):
        return "ok"
    if ok == 0:
        return "failed"
    return "partial"


def reading(row: dict[str, Any], label: str) -> dict[str, Any] | None:
    for item in row.get("readings", []):
        if item["label"] == label:
            return item
    return None


def point_delta(row: dict[str, Any], label: str, field: str = "rss_mb") -> float | None:
    """The reading with `label` minus the reading taken just before it.

    The first reading has no earlier one, so its own value is returned."""
    items = row.get("readings", [])
    for index, item in enumerate(items):
        if item["label"] == label:
            if index == 0:
                return float(item[field])
            return float(item[field]) - float(items[index - 1][field])
    return None


def primary(row: dict[str, Any]) -> float | None:
    """The one number that stands for a run: the delta of its last reading,
    or the final RSS for the runs that build many steps."""
    items = row.get("readings", [])
    if not items:
        return None
    if row.get("point") in WHOLE_RUN_POINTS:
        return float(items[-1]["rss_mb"])
    return point_delta(row, items[-1]["label"])
