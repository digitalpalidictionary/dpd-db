"""Get basic day, date, time info."""

from datetime import datetime

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
    """ Make current time iso-formatted UTC datetime string """
    now = datetime.utcnow().replace(microsecond=0)
    return now.isoformat()
