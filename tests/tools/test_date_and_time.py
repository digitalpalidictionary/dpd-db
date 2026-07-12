"""Tests for tools/date_and_time.py timestamp formatting.

`now` is computed once at module import, so it is monkeypatched to a fixed
datetime for the format functions. `make_timestamp` computes its own fresh
`datetime.now(UTC)` internally, so it is checked against a shape regex
instead (time-dependent, not an exact value).
"""

import re
from datetime import datetime

import pytest

import tools.date_and_time as date_and_time


@pytest.fixture
def fixed_now(monkeypatch: pytest.MonkeyPatch) -> datetime:
    frozen = datetime(2026, 7, 11, 9, 5)
    monkeypatch.setattr(date_and_time, "now", frozen)
    return frozen


def test_year_month_day_hour_minute_dash(fixed_now: datetime) -> None:
    assert date_and_time.year_month_day_hour_minute_dash() == "2026-07-11-09-05"


def test_year_month_day_dash(fixed_now: datetime) -> None:
    assert date_and_time.year_month_day_dash() == "2026-07-11"


def test_year_month_day(fixed_now: datetime) -> None:
    assert date_and_time.year_month_day() == "20260711"


def test_hour_minute(fixed_now: datetime) -> None:
    assert date_and_time.hour_minute() == "09:05"


def test_day(fixed_now: datetime) -> None:
    assert date_and_time.day() == "11"


def test_make_timestamp_matches_iso_shape() -> None:
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", date_and_time.make_timestamp()
    )


def test_make_timestamp_has_no_microseconds_or_tzinfo() -> None:
    timestamp = date_and_time.make_timestamp()
    assert "." not in timestamp
    assert "+" not in timestamp
    assert not timestamp.endswith("Z")
