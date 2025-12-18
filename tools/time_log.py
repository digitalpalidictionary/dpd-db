# -*- coding: utf-8 -*-
import os
from enum import Enum
from pathlib import Path
from string import Template
from datetime import datetime
from datetime import timedelta

s = os.getenv("LOG_TIME")
if s is not None and s.lower() == "true":
    LOG_TIME = True
else:
    LOG_TIME = False

LOG_FILE = Path("time_log.dat")

# https://stackoverflow.com/questions/8906926/formatting-timedelta-objects#49226644


class DeltaTemplate(Template):
    delimiter = "%"


def strfdelta(td: timedelta, fmt="%H:%M:%S") -> str:
    # Get the timedelta’s sign and absolute number of seconds.
    sign = "-" if td.days < 0 else "+"
    secs = abs(td).total_seconds()

    # Break the seconds into more readable quantities.
    days, rem = divmod(secs, 86400)  # Seconds per day: 24 * 60 * 60
    hours, rem = divmod(rem, 3600)  # Seconds per hour: 60 * 60
    mins, secs = divmod(rem, 60)

    # Format (as per above answers) and return the result string.
    t = DeltaTemplate(fmt)
    return t.substitute(
        s=sign,
        D="{:d}".format(int(days)),
        H="{:02d}".format(int(hours)),
        M="{:02d}".format(int(mins)),
        S="{:02d}".format(int(secs)),
    )


class LogPrecision(str, Enum):
    Seconds = "s"
    Micro = "µs"


class TimeLog:
    def __init__(self, precision=LogPrecision.Seconds):
        self.t0 = datetime.now()
        self.t_prev = self.t0
        self.precision = precision

    def start(self, start_new=True):
        if not LOG_TIME:
            return

        self.t0 = datetime.now()

        if start_new and LOG_FILE.exists():
            LOG_FILE.unlink()

    def log(self, msg: str, trim=True):
        if not LOG_TIME:
            return

        if trim and len(msg) > 30:
            msg = msg[0:30]

        now = datetime.now()
        delta = now - self.t0
        delta_prev = now - self.t_prev
        self.t_prev = now

        dat_msg = msg.replace("_", "\\\\_")

        if self.precision == LogPrecision.Seconds:
            t = delta.seconds
            tp = delta_prev.seconds
        elif self.precision == LogPrecision.Micro:
            t = delta.microseconds
            tp = delta_prev.microseconds
        else:
            t = delta.seconds
            tp = delta_prev.seconds

        dat_line = f"{t}\t{tp}\t{dat_msg}\n"

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(dat_line)

        print(f"{strfdelta(delta)} {tp}{self.precision.value} {msg}")
