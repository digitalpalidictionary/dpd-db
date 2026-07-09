"""Get basic day, date, time info."""

from datetime import UTC, datetime

now = datetime.now()


def year_month_day_hour_minute_dash():
    return now.strftime("%Y-%m-%d-%H-%M")


def year_month_day_dash():
    return now.strftime("%Y-%m-%d")


def year_month_day():
    return now.strftime("%Y%m%d")


def hour_minute():
    return now.strftime("%H:%M")


def day():
    return now.strftime("%d")


def make_timestamp() -> str:
    """Make current time iso-formatted UTC datetime string"""
    now = datetime.now(UTC).replace(microsecond=0, tzinfo=None)
    return now.isoformat()
