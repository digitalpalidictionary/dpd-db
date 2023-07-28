"""Get basic day, date, time info."""

from datetime import datetime

now = datetime.now()


def date_and_time():
    return now.strftime("%Y-%m-%d")


def hour_minute():
    return now.strftime("%H:%M")


def day():
    return now.strftime("%d")
