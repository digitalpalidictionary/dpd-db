"""Write the contributor dashboard: who is in the editor, when each contributor
was online, how many words they added, and how full the server is.

Run by cron every minute on the contributor server. The page is one static
HTML file that nginx serves at /dashboard/ behind the maintainer's login.
Design: kamma/threads/20261113_contrib_usage_page/spec.md.
"""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta, tzinfo
from enum import Enum
from pathlib import Path

import psutil

USER_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,31}")
UNIT_PATTERN = re.compile(r"dpd-gui@([a-z][a-z0-9_]{0,31})\.service")
UNIT_EXIT_PATTERN = re.compile(
    r"dpd-gui@[a-z0-9_]+\.service: (Main process exited|Failed with result|Deactivated successfully)"
)
ASLEEP_PATTERN = re.compile(r"lifecycle: asleep: ([0-9]+(?:\.[0-9]+)?) min idle")
CONNECT_MESSAGES = ("lifecycle: page connected", "lifecycle: page reconnected")
TEST_USERS: tuple[str, ...] = ("bdhrs", "deva")
HISTORY_DAYS = 14
# Day and Week are drawn as timelines of single visits, ending now at the
# right edge. Month, Year and All are bar charts of saved minutes per day.
TIMELINE_SPANS: dict[str, timedelta] = {
    "day": timedelta(hours=24),
    "week": timedelta(days=7),
}
BAR_PERIODS: tuple[str, ...] = ("month", "year", "all")
PERIODS: tuple[str, ...] = ("day", "week", "month", "year", "all")
PERIOD_NAMES: dict[str, str] = {
    "day": "today",
    "week": "last 7 days",
    "month": "last 30 days",
    "year": "last 12 months",
    "all": "all time",
}
MONTH_DAYS = 30
YEAR_WEEKS = 52
# The journal still holds these days, so each run counts them again. Older
# days keep what an earlier run saved, so history outlives the journal.
REFRESH_DAYS = 7
TICK_HOURS = 3
# The most labels a bar ruler shows; more would run into each other.
MAX_BAR_LABELS = 8
# Keeps a label clear of the "now" label at the right edge.
LABEL_CLEAR_PERCENT = 8.0
RELOAD_SECONDS = 60
WARN_PERCENT = 70
BAD_PERCENT = 90
# A visit that is a few seconds long would be invisible on a 24-hour track.
MIN_BLOCK_PERCENT = 0.35

LOGO_SOURCE = Path("identity/logo/dpd-logo-dark.svg")
FONT_SOURCE = Path("identity/fonts/Inter-VariableFont_opsz,wght.ttf")
CSS_VARIABLES_SOURCE = Path("identity/css/dpd-variables.css")
LOGO_NAME = "dpd-logo-dark.svg"
FONT_NAME = "Inter.ttf"


class Kind(Enum):
    CONNECT = "connect"
    COUNTDOWN = "countdown"
    CANCEL = "cancel"
    ASLEEP = "asleep"
    STOPPED = "stopped"
    STARTED = "started"


@dataclass(frozen=True)
class Event:
    at: datetime
    user: str
    kind: Kind
    idle_minutes: float = 0.0


@dataclass
class Visit:
    user: str
    start: datetime
    # None while the page is still open.
    end: datetime | None = None
    countdown: bool = False


class State(Enum):
    ONLINE = "online"
    SLEEPING_SOON = "going to sleep"
    ASLEEP = "asleep"
    DOWN = "down"


@dataclass(frozen=True)
class Unit:
    user: str
    active: bool
    memory_bytes: int | None


@dataclass(frozen=True)
class Block:
    start: datetime
    end: datetime
    is_open: bool


@dataclass(frozen=True)
class Bucket:
    label: str
    title: str
    first: date
    last: date


@dataclass(frozen=True)
class Bar:
    bucket: Bucket
    minutes: int
    words: int


@dataclass(frozen=True)
class LaneView:
    """One lane in one period: blocks for a timeline, bars for a bar chart."""

    minutes: int
    words: int
    blocks: list[Block] = field(default_factory=list)
    bars: list[Bar] = field(default_factory=list)


@dataclass(frozen=True)
class Lane:
    user: str
    state: State
    views: dict[str, LaneView]
    words_total: int
    memory_bytes: int | None
    is_test: bool
    online_since: datetime | None
    last_seen: datetime | None
    added: datetime | None = None


@dataclass(frozen=True)
class Meter:
    label: str
    used: float
    total: float
    unit: str

    @property
    def percent(self) -> float:
        if self.total <= 0:
            return 0.0
        return min(100.0, 100.0 * self.used / self.total)


@dataclass(frozen=True)
class Dashboard:
    now: datetime
    lanes: list[Lane]
    meters: list[Meter]
    period_words: dict[str, int]
    period_starts: dict[str, date]
    words_total: int
    first_day: str | None
    test_users: list[str] = field(default_factory=list)


# ----- journal → events → visits -----


def _user_of(record: dict[str, object]) -> str | None:
    # Editor lines carry the unit in _SYSTEMD_UNIT; systemd's own Started and
    # Stopped lines run in init.scope and name the unit in UNIT.
    for key in ("_SYSTEMD_UNIT", "UNIT"):
        value = record.get(key)
        if isinstance(value, str) and (match := UNIT_PATTERN.fullmatch(value)):
            return match.group(1)
    return None


def _kind_of(message: str) -> tuple[Kind, float] | None:
    if message in CONNECT_MESSAGES:
        return Kind.CONNECT, 0.0
    if message.startswith("lifecycle: countdown shown"):
        return Kind.COUNTDOWN, 0.0
    if message == "lifecycle: countdown cancelled":
        return Kind.CANCEL, 0.0
    if match := ASLEEP_PATTERN.match(message):
        return Kind.ASLEEP, float(match.group(1))
    # A process that dies ends the visit even when no Started line follows,
    # e.g. a unit that hit its start limit and stays failed.
    if message.startswith("Stopped dpd-gui@") or UNIT_EXIT_PATTERN.match(message):
        return Kind.STOPPED, 0.0
    if message.startswith("Started dpd-gui@"):
        return Kind.STARTED, 0.0
    return None


def parse_journal(lines: Iterable[str], tz: tzinfo) -> list[Event]:
    """Turn `journalctl -o json` lines into the events a visit is built from,
    oldest first. Every other line is skipped."""
    events: list[Event] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        message = record.get("MESSAGE")
        # journald gives a message that is not valid UTF-8 as a list of bytes.
        if not isinstance(message, str):
            continue
        found = _kind_of(message)
        user = _user_of(record)
        stamp = record.get("__REALTIME_TIMESTAMP")
        if found is None or user is None or not isinstance(stamp, str):
            continue
        kind, idle_minutes = found
        at = datetime.fromtimestamp(int(stamp) / 1_000_000, tz)
        events.append(Event(at, user, kind, idle_minutes))
    events.sort(key=lambda event: event.at)
    return events


def build_visits(events: Iterable[Event]) -> list[Visit]:
    """A visit starts at the first page connect and ends at the last action
    before sleep, or at a stop or restart of the editor."""
    visits: list[Visit] = []
    current: dict[str, Visit] = {}
    for event in events:
        visit = current.get(event.user)
        if event.kind is Kind.CONNECT:
            if visit is None:
                visit = Visit(event.user, event.at)
                current[event.user] = visit
                visits.append(visit)
            continue
        if visit is None:
            continue
        if event.kind is Kind.COUNTDOWN:
            visit.countdown = True
        elif event.kind is Kind.CANCEL:
            visit.countdown = False
        else:
            if event.kind is Kind.ASLEEP:
                # The asleep line comes after the idle wait; the person left
                # when the idle time began.
                last_action = event.at - timedelta(minutes=event.idle_minutes)
                visit.end = max(visit.start, last_action)
            else:
                visit.end = event.at
            visit.countdown = False
            del current[event.user]
    return visits


def blocks_in_window(
    visits: Iterable[Visit], window_start: datetime, now: datetime
) -> list[Block]:
    """The visits cut to the part between window_start and now."""
    blocks: list[Block] = []
    for visit in visits:
        end = now if visit.end is None else min(visit.end, now)
        start = max(visit.start, window_start)
        if end < start or (visit.end is not None and end <= window_start):
            continue
        blocks.append(Block(start, end, visit.end is None))
    return blocks


def lane_state(unit: Unit | None, open_visit: Visit | None) -> State:
    if unit is None or not unit.active:
        return State.DOWN
    if open_visit is None:
        return State.ASLEEP
    if open_visit.countdown:
        return State.SLEEPING_SOON
    return State.ONLINE


def seconds_per_day(
    visits: Iterable[Visit], now: datetime
) -> dict[str, dict[str, int]]:
    """Seconds online per user per calendar day. A visit across midnight
    counts on both days; an open visit counts up to now. Seconds, not minutes:
    rounding each day to a minute made a month add up to less than its week."""
    seconds: dict[str, dict[str, float]] = {}
    for visit in visits:
        start = visit.start
        end = visit.end or now
        while start < end:
            midnight = datetime.combine(
                start.date() + timedelta(days=1), time(), start.tzinfo
            )
            piece_end = min(end, midnight)
            days = seconds.setdefault(visit.user, {})
            day = start.date().isoformat()
            days[day] = days.get(day, 0.0) + (piece_end - start).total_seconds()
            start = piece_end
    whole: dict[str, dict[str, int]] = {}
    for user, days in seconds.items():
        kept = {day: round(value) for day, value in days.items() if round(value)}
        if kept:
            whole[user] = kept
    return whole


def journal_start(lines: Iterable[str], tz: tzinfo) -> datetime | None:
    """The time of the first line the journal read returned, or None when it
    returned nothing (a failed read, or a journal that was cleared)."""
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        stamp = record.get("__REALTIME_TIMESTAMP") if isinstance(record, dict) else None
        if isinstance(stamp, str) and stamp.isdigit():
            return datetime.fromtimestamp(int(stamp) / 1_000_000, tz)
    return None


def merge_seconds(
    stored: dict[str, dict[str, int]],
    fresh: dict[str, dict[str, int]],
    now: datetime,
    covered_from: datetime | None,
) -> dict[str, dict[str, int]]:
    """A day is counted again from this run's journal read only when the read
    covered the whole day (it began at or before that midnight). The last
    REFRESH_DAYS covered days are always recounted: an open visit can shrink
    when it ends. An older covered day is filled only when nothing was saved
    for it. Every day the read did not cover keeps what was saved, so a
    rotated or failed journal never erases history. Never "keep the larger":
    a sleep line rightly shortens an earlier estimate."""

    def covered(day: str) -> bool:
        if covered_from is None:
            return False
        midnight = datetime.combine(
            date.fromisoformat(day), time(), covered_from.tzinfo
        )
        return covered_from <= midnight

    recent = {
        (now.date() - timedelta(days=back)).isoformat() for back in range(REFRESH_DAYS)
    }
    refresh = {day for day in recent if covered(day)}
    merged: dict[str, dict[str, int]] = {}
    for user in sorted(set(stored) | set(fresh)):
        days = {
            day: value
            for day, value in stored.get(user, {}).items()
            if day not in refresh
        }
        for day, value in fresh.get(user, {}).items():
            if day in refresh or (day not in days and covered(day)):
                days[day] = value
        if days:
            merged[user] = dict(sorted(days.items()))
    return merged


def read_seconds(path: Path) -> dict[str, dict[str, int]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _set_aside(path, str(exc))
        return {}
    if not isinstance(data, dict):
        _set_aside(path, f"top level is {type(data).__name__}, not an object")
        return {}
    seconds: dict[str, dict[str, int]] = {}
    for user, days in data.items():
        if isinstance(user, str) and isinstance(days, dict):
            seconds[user] = {
                day: value
                for day, value in days.items()
                if isinstance(day, str) and isinstance(value, int)
            }
    return seconds


def _set_aside(path: Path, reason: str) -> None:
    """Keep a damaged file for a look, under a name of its own so an older
    damaged copy is never overwritten; a fresh file starts from the journal."""
    corrupt = path.with_name(f"{path.name}.corrupt.{datetime.now():%Y%m%d%H%M%S%f}")
    try:
        path.replace(corrupt)
    except OSError as exc:
        print(f"{path.name} unreadable ({reason}); could not set it aside: {exc}")
        return
    print(f"{path.name} unreadable ({reason}), kept as {corrupt.name}")


def write_seconds(path: Path, seconds: dict[str, dict[str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(seconds, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def first_day(
    words: dict[str, dict[str, int]], seconds: dict[str, dict[str, int]], today: date
) -> date:
    """The earliest day any user has words or time online; the start of All."""
    days = [
        day
        for source in (words, seconds)
        for per_day in source.values()
        for day in per_day
    ]
    parsed: list[date] = []
    for day in days:
        try:
            parsed.append(date.fromisoformat(day))
        except ValueError:
            continue
    return min([today, *parsed])


def period_starts(today: date, start_of_all: date) -> dict[str, date]:
    """The first calendar day each period counts words (and bar minutes) from."""
    monday = today - timedelta(days=today.weekday())
    return {
        "day": today,
        "week": today - timedelta(days=6),
        "month": today - timedelta(days=MONTH_DAYS - 1),
        "year": monday - timedelta(weeks=YEAR_WEEKS - 1),
        "all": start_of_all.replace(day=1),
    }


def bar_buckets(period: str, today: date, start_of_all: date) -> list[Bucket]:
    if period == "month":
        days = [today - timedelta(days=back) for back in range(MONTH_DAYS - 1, -1, -1)]
        return [Bucket(f"{d.day} {d:%b}", f"{d:%a} {d.day} {d:%b}", d, d) for d in days]
    if period == "year":
        monday = today - timedelta(days=today.weekday())
        weeks = [
            monday - timedelta(weeks=back) for back in range(YEAR_WEEKS - 1, -1, -1)
        ]
        return [
            Bucket(
                f"{w:%b}", f"week of {w.day} {w:%b} {w:%Y}", w, w + timedelta(days=6)
            )
            for w in weeks
        ]
    buckets: list[Bucket] = []
    month = start_of_all.replace(day=1)
    while month <= today:
        following = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
        label = f"{month:%b %y}"
        buckets.append(
            Bucket(label, f"{month:%B %Y}", month, following - timedelta(days=1))
        )
        month = following
    return buckets


def _sum_days(per_day: dict[str, int], first: date, last: date) -> int:
    low, high = first.isoformat(), last.isoformat()
    return sum(value for day, value in per_day.items() if low <= day <= high)


def build_lanes(
    users: list[str],
    units: dict[str, Unit],
    visits: list[Visit],
    words: dict[str, dict[str, int]],
    seconds: dict[str, dict[str, int]],
    test_users: set[str],
    now: datetime,
    added: dict[str, datetime] | None = None,
) -> list[Lane]:
    """One lane per user: real contributors first, test users last, each group
    by name, so a lane never moves between reloads."""
    today = now.date()
    start_of_all = first_day(words, seconds, today)
    starts = period_starts(today, start_of_all)
    buckets = {
        period: bar_buckets(period, today, start_of_all) for period in BAR_PERIODS
    }
    lanes: list[Lane] = []
    for user in sorted(users, key=lambda name: (name in test_users, name)):
        own = [visit for visit in visits if visit.user == user]
        open_visit = next((visit for visit in own if visit.end is None), None)
        unit = units.get(user)
        ended = [visit.end for visit in own if visit.end is not None]
        user_words = words.get(user, {})
        user_seconds = seconds.get(user, {})
        views: dict[str, LaneView] = {}
        for period, span in TIMELINE_SPANS.items():
            blocks = blocks_in_window(own, now - span, now)
            online = sum((block.end - block.start).total_seconds() for block in blocks)
            views[period] = LaneView(
                minutes=round(online / 60),
                words=_sum_days(user_words, starts[period], today),
                blocks=blocks,
            )
        for period in BAR_PERIODS:
            bars = [
                Bar(
                    bucket,
                    round(_sum_days(user_seconds, bucket.first, bucket.last) / 60),
                    _sum_days(user_words, bucket.first, bucket.last),
                )
                for bucket in buckets[period]
            ]
            first, last = buckets[period][0].first, buckets[period][-1].last
            views[period] = LaneView(
                # Rounded once over the whole period, like the timelines.
                minutes=round(_sum_days(user_seconds, first, last) / 60),
                words=sum(bar.words for bar in bars),
                bars=bars,
            )
        lanes.append(
            Lane(
                user=user,
                state=lane_state(unit, open_visit),
                views=views,
                words_total=sum(user_words.values()),
                memory_bytes=unit.memory_bytes if unit else None,
                is_test=user in test_users,
                online_since=open_visit.start if open_visit else None,
                last_seen=max(ended) if ended else None,
                added=(added or {}).get(user),
            )
        )
    return lanes


# ----- other readers -----


def parse_daily_log(text: str) -> dict[str, int]:
    """The editor's `daily_log_<user>.json` as words per day (all counters added)."""
    data = json.loads(text)
    per_day: dict[str, int] = {}
    if not isinstance(data, dict):
        return per_day
    for day, counts in data.items():
        if isinstance(counts, dict):
            per_day[day] = sum(
                value for value in counts.values() if isinstance(value, int)
            )
    return per_day


def read_daily_logs(data_dir: Path) -> dict[str, dict[str, int]]:
    words: dict[str, dict[str, int]] = {}
    for path in sorted(data_dir.glob("daily_log_*.json")):
        user = path.stem.removeprefix("daily_log_")
        if not USER_PATTERN.fullmatch(user):
            continue
        try:
            words[user] = parse_daily_log(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"skipped {path.name}: {exc}")
    return words


def read_users(env_dir: Path) -> list[str]:
    """Every contributor has `/etc/dpd/<user>.env` (add_contributor.sh)."""
    return sorted(
        path.stem for path in env_dir.glob("*.env") if USER_PATTERN.fullmatch(path.stem)
    )


def read_added(env_dir: Path, users: list[str], tz: tzinfo) -> dict[str, datetime]:
    """When each account was added: its env file's time. Editing the file (the
    idle kill switch) moves it, which only changes the "added" wording of a
    lane that was never seen."""
    added: dict[str, datetime] = {}
    for user in users:
        try:
            added[user] = datetime.fromtimestamp(
                (env_dir / f"{user}.env").stat().st_mtime, tz
            )
        except OSError:
            continue
    return added


def parse_systemctl_show(text: str) -> dict[str, Unit]:
    units: dict[str, Unit] = {}
    for block in text.strip().split("\n\n"):
        values: dict[str, str] = {}
        for line in block.splitlines():
            key, _, value = line.partition("=")
            values[key] = value
        match = UNIT_PATTERN.fullmatch(values.get("Id", ""))
        if not match:
            continue
        memory = values.get("MemoryCurrent", "")
        units[match.group(1)] = Unit(
            user=match.group(1),
            # "activating" covers the 10 s auto-restart after every sleep;
            # counting it as down would flash a red lane once a sleep.
            active=values.get("ActiveState") in ("active", "activating", "reloading"),
            memory_bytes=int(memory) if memory.isdigit() else None,
        )
    return units


def read_units(users: list[str]) -> dict[str, Unit]:
    if not users:
        return {}
    result = subprocess.run(
        ["systemctl", "show", "-p", "Id", "-p", "ActiveState", "-p", "MemoryCurrent"]
        + [f"dpd-gui@{user}.service" for user in users],
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_systemctl_show(result.stdout)


def read_journal(since: datetime) -> list[str]:
    result = subprocess.run(
        [
            "journalctl",
            "-u",
            "dpd-gui@*",
            "--since",
            since.strftime("%Y-%m-%d %H:%M:%S"),
            "-o",
            "json",
            "--output-fields=MESSAGE,_SYSTEMD_UNIT,UNIT",
            "--no-pager",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # journalctl exits 1 when no unit matches yet ("No data available"); the
    # page must still be written, with every lane asleep.
    if result.returncode != 0:
        print(f"journalctl exit {result.returncode}: {result.stderr.strip()}")
    return result.stdout.splitlines()


def read_meters() -> list[Meter]:
    gib = 1024**3
    disk = psutil.disk_usage("/")
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    cores = psutil.cpu_count() or 1
    return [
        Meter("Disk", disk.used / gib, disk.total / gib, "GB"),
        Meter(
            "Memory", (memory.total - memory.available) / gib, memory.total / gib, "GB"
        ),
        Meter("Swap", swap.used / gib, swap.total / gib, "GB"),
        Meter("CPU load", psutil.getloadavg()[1], cores, "cores"),
    ]


def build_dashboard(
    lanes: list[Lane],
    meters: list[Meter],
    words: dict[str, dict[str, int]],
    seconds: dict[str, dict[str, int]],
    test_users: set[str],
    now: datetime,
) -> Dashboard:
    """The big numbers count real contributors only, including any who no
    longer have a lane."""
    today = now.date()
    starts = period_starts(today, first_day(words, seconds, today))
    real = {user: days for user, days in words.items() if user not in test_users}
    days_with_words = sorted(
        day for days in real.values() for day, count in days.items() if count
    )
    return Dashboard(
        now=now,
        lanes=lanes,
        meters=meters,
        period_words={
            period: sum(
                _sum_days(days, starts[period], today) for days in real.values()
            )
            for period in PERIODS
        },
        period_starts=starts,
        words_total=sum(sum(days.values()) for days in real.values()),
        first_day=days_with_words[0] if days_with_words else None,
        test_users=sorted(test_users),
    )


# ----- page -----

PAGE_CSS = """
@font-face {
  font-family: "Inter";
  src: url("Inter.ttf") format("truetype-variations");
  font-weight: 100 900;
}
:root {
  color-scheme: dark;
  --bg: var(--dark);
  --card: var(--dark-shade);
  --text: var(--light);
  --muted: hsl(198, 25%, 62%);
  --line: hsla(198, 100%, 50%, 0.16);
  --track: hsla(198, 100%, 50%, 0.07);
  --tick: hsla(198, 100%, 70%, 0.12);
  --ok: hsl(150, 80%, 45%);
  --warn: hsl(38, 100%, 55%);
  --bad: hsl(0, 85%, 62%);
  --idle: hsl(198, 10%, 45%);
}
@media (prefers-color-scheme: light) {
  :root {
    color-scheme: light;
    --bg: var(--light);
    --card: hsl(198, 100%, 99%);
    --text: var(--dark);
    --muted: hsl(198, 25%, 35%);
    --line: hsla(198, 100%, 35%, 0.18);
    --track: hsla(198, 100%, 40%, 0.07);
    --tick: hsla(198, 100%, 30%, 0.12);
    --ok: hsl(150, 80%, 33%);
    --warn: hsl(32, 100%, 42%);
    --bad: hsl(0, 75%, 48%);
    --idle: hsl(198, 10%, 60%);
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: "Inter", system-ui, sans-serif;
  font-size: 15px;
  line-height: 1.4;
}
main { max-width: 1200px; margin: 0 auto; padding: 24px 16px 48px; }
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 20px 22px;
}
.section-title {
  margin: 32px 0 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}

header { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
header img { width: 52px; height: 52px; }
header h1 { margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.01em; }
header .sub { color: var(--muted); font-size: 13px; }
header .presence {
  margin-left: auto;
  display: flex; align-items: center; gap: 10px;
  padding: 8px 16px;
  border: 1px solid var(--line);
  border-radius: 999px;
  font-weight: 600;
}

.numbers { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-top: 24px; }
.number .value {
  font-size: clamp(44px, 9vw, 76px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.03em;
  color: var(--primary);
  font-variant-numeric: tabular-nums;
}
.number .label { margin-top: 10px; font-size: 16px; font-weight: 600; }
.number .note { color: var(--muted); font-size: 13px; }

.meters { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.meter .top { display: flex; justify-content: space-between; align-items: baseline; }
.meter .name { font-weight: 600; }
.meter .pct { font-size: 22px; font-weight: 700; font-variant-numeric: tabular-nums; }
.meter .bar {
  margin: 10px 0 8px;
  height: 10px;
  border-radius: 999px;
  background: var(--track);
  overflow: hidden;
}
.meter .fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--primary-alt), var(--primary));
}
.meter.warn .fill { background: var(--warn); }
.meter.bad .fill { background: var(--bad); }
.meter.warn .pct { color: var(--warn); }
.meter.bad .pct { color: var(--bad); }
.meter .detail { color: var(--muted); font-size: 13px; font-variant-numeric: tabular-nums; }

.lanes { padding: 8px 22px 14px; }
.row {
  display: grid;
  grid-template-columns: 230px 1fr 250px;
  gap: 18px;
  align-items: center;
  padding: 12px 0;
  border-top: 1px solid var(--line);
}
.row.ruler { border-top: none; padding: 10px 0 4px; }
.row.test-first { border-top: 1px dashed var(--line); margin-top: 6px; }
.who { display: flex; align-items: center; gap: 12px; min-width: 0; }
.who .name { font-weight: 650; font-size: 16px; overflow-wrap: anywhere; }
.who .state { font-size: 13px; color: var(--muted); }
.tag {
  margin-left: 6px;
  padding: 1px 7px;
  border: 1px solid var(--line);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  vertical-align: 2px;
}
.dot {
  flex: none;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--idle);
}
.online .dot { background: var(--ok); animation: pulse 2s ease-out infinite; }
.sleeping-soon .dot { background: var(--warn); }
.down .dot { background: var(--bad); }
.online .state { color: var(--ok); font-weight: 600; }
.sleeping-soon .state { color: var(--warn); font-weight: 600; }
.down .state { color: var(--bad); font-weight: 600; }
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 hsla(150, 80%, 45%, 0.6); }
  80%, 100% { box-shadow: 0 0 0 9px hsla(150, 80%, 45%, 0); }
}
@media (prefers-reduced-motion: reduce) { .dot { animation: none !important; } }

.track {
  position: relative;
  height: 34px;
  border-radius: 9px;
  background: var(--track);
}
.tick { position: absolute; top: 0; bottom: 0; width: 1px; background: var(--tick); }
.tick.midnight { background: var(--muted); opacity: 0.6; }
.block {
  position: absolute;
  top: 6px; bottom: 6px;
  border-radius: 5px;
  background: var(--primary);
}
.block.open { background: var(--ok); box-shadow: 0 0 12px hsla(150, 80%, 45%, 0.55); }
.hours { position: relative; height: 16px; font-size: 11px; color: var(--muted); }
.hours span { position: absolute; transform: translateX(-50%); font-variant-numeric: tabular-nums; }
.hours span.midnight { color: var(--text); font-weight: 600; }
.hours span.now-label { transform: translateX(-100%); color: var(--text); font-weight: 600; }

.sleeping-soon .block.open { background: var(--warn); box-shadow: none; }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; text-align: right; }
.stats b { display: block; font-size: 18px; font-weight: 700; font-variant-numeric: tabular-nums; }
.stats span {
  font-size: 10px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}
.empty { color: var(--muted); padding: 16px 0; }

.view, [data-for] { display: none; }
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin: 32px 0 12px;
}
.section-head .section-title { margin: 0; }
.views {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--card);
}
.views button {
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  background: none;
  border: 0;
  border-radius: 999px;
  padding: 6px 14px;
  cursor: pointer;
}
.views button:hover { color: var(--text); }
.views button[aria-pressed="true"] { background: var(--primary); color: var(--dark); }
.track.bars { display: flex; align-items: flex-end; gap: 2px; padding: 4px 6px; }
.bar-slot { flex: 1; height: 100%; display: flex; align-items: flex-end; }
.vbar { width: 100%; border-radius: 2px 2px 0 0; background: var(--primary); }

@media (max-width: 860px) {
  .row { grid-template-columns: 1fr; gap: 10px; }
  .row.ruler .who, .row.ruler .stats { display: none; }
  .stats { text-align: left; justify-items: start; }
}
@media (max-width: 520px) {
  main { padding-top: 16px; }
  .card { padding: 16px; }
  .lanes { padding: 4px 16px 10px; }
  .meters { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .numbers { gap: 12px; }
  header .presence { margin-left: 0; }
}
"""


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _clock(at: datetime) -> str:
    return at.strftime("%H:%M")


def _when(at: datetime, now: datetime) -> str:
    if at.date() == now.date():
        return _clock(at)
    if at.date() == now.date() - timedelta(days=1):
        return f"yesterday {_clock(at)}"
    return f"{at.day} {at.strftime('%b')}"


def _day(at: datetime, now: datetime) -> str:
    if at.date() == now.date():
        return "today"
    if at.date() == now.date() - timedelta(days=1):
        return "yesterday"
    return f"{at.day} {at.strftime('%b')}"


def _megabytes(value: int | None) -> str:
    if value is None:
        return ""
    # A no-break space, so the number and its unit never split across lines.
    return f"{value / 1024**2:,.0f}\u00a0MB"


def _state_text(lane: Lane, now: datetime) -> str:
    memory = _megabytes(lane.memory_bytes)
    if lane.state is State.ONLINE and lane.online_since:
        text = f"online since {_clock(lane.online_since)}"
    elif lane.state is State.SLEEPING_SOON:
        text = "idle, going to sleep"
    elif lane.state is State.DOWN:
        text = "down"
    elif lane.last_seen:
        text = f"asleep, last seen {_when(lane.last_seen, now)}"
    elif lane.added and now - lane.added <= timedelta(days=HISTORY_DAYS):
        text = f"added {_day(lane.added, now)}, not seen yet"
    else:
        text = f"asleep, not seen in {HISTORY_DAYS} days"
    return f"{text} · {memory}" if memory and lane.state is not State.DOWN else text


def _percent(at: datetime, window_start: datetime, span: timedelta) -> float:
    return 100.0 * (at - window_start) / span


def tick_times(
    window_start: datetime, now: datetime, every_hours: int = TICK_HOURS
) -> list[datetime]:
    """Every clock hour divisible by every_hours inside the window (24 gives
    the midnights)."""
    tick = window_start.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    ticks: list[datetime] = []
    while tick < now:
        if tick.hour % every_hours == 0:
            ticks.append(tick)
        tick += timedelta(hours=1)
    return ticks


def _now_label() -> str:
    return '<span class="now-label" style="left:100%">now</span>'


def _timeline_ruler(period: str, window_start: datetime, ticks: list[datetime]) -> str:
    span = TIMELINE_SPANS[period]
    labels: list[str] = []
    for tick in ticks:
        if period == "day":
            left = _percent(tick, window_start, span)
            # Midnight shows the day that starts there.
            text, css = (
                (f"{tick:%a}", "midnight")
                if tick.hour == 0
                else (f"{tick.hour:02d}", "")
            )
        else:
            # A week label sits in the middle of its day.
            left = _percent(tick + timedelta(hours=12), window_start, span)
            text, css = f"{tick:%a} {tick.day}", ""
        if left > 100 - LABEL_CLEAR_PERCENT:
            continue
        labels.append(f'<span class="{css}" style="left:{left:.3f}%">{text}</span>')
    return "".join(labels) + _now_label()


def _bars_ruler(buckets: list[Bucket]) -> str:
    count = len(buckets)
    step = max(1, -(-count // MAX_BAR_LABELS))
    labels: list[str] = []
    for index, bucket in enumerate(buckets):
        left = 100.0 * (index + 0.5) / count
        if index % step or left > 100 - LABEL_CLEAR_PERCENT:
            continue
        labels.append(f'<span style="left:{left:.3f}%">{_esc(bucket.label)}</span>')
    return "".join(labels) + _now_label()


def _render_timeline(
    blocks: list[Block], window_start: datetime, span: timedelta, ticks: list[datetime]
) -> str:
    time_format = "%H:%M" if span <= timedelta(hours=24) else "%a %H:%M"
    parts: list[str] = [
        f'<div class="tick{" midnight" if tick.hour == 0 else ""}" '
        f'style="left:{_percent(tick, window_start, span):.3f}%"></div>'
        for tick in ticks
    ]
    for block in blocks:
        left = _percent(block.start, window_start, span)
        width = max(MIN_BLOCK_PERCENT, _percent(block.end, window_start, span) - left)
        minutes = round((block.end - block.start).total_seconds() / 60)
        end_text = "now" if block.is_open else _clock(block.end)
        title = f"{block.start.strftime(time_format)} – {end_text} · {minutes} min"
        css = "block open" if block.is_open else "block"
        parts.append(
            f'<div class="{css}" style="left:{left:.3f}%;width:{width:.3f}%" '
            f'title="{_esc(title)}"></div>'
        )
    return f'<div class="track">{"".join(parts)}</div>'


def _render_bars(bars: list[Bar], top: int) -> str:
    parts: list[str] = []
    for bar in bars:
        height = max(4.0, 100.0 * bar.minutes / top) if bar.minutes else 0.0
        title = f"{bar.bucket.title}: {bar.minutes:,} min, {bar.words:,} words"
        parts.append(
            f'<div class="bar-slot" title="{_esc(title)}">'
            f'<div class="vbar" style="height:{height:.1f}%"></div></div>'
        )
    return f'<div class="track bars">{"".join(parts)}</div>'


def _render_lane(
    lane: Lane, period: str, first_test: bool, track: str, now: datetime
) -> str:
    view = lane.views[period]
    state_css = lane.state.name.lower().replace("_", "-")
    classes = f"row {state_css}" + (" test-first" if first_test else "")
    tag = '<span class="tag">test</span>' if lane.is_test else ""
    words_label = "today" if period == "day" else "words"
    return (
        f'<div class="{classes}">'
        f'<div class="who"><span class="dot"></span><div>'
        f'<div class="name">{_esc(lane.user)}{tag}</div>'
        f'<div class="state">{_esc(_state_text(lane, now))}</div>'
        f"</div></div>"
        f"{track}"
        f'<div class="stats">'
        f"<div><b>{view.minutes:,}</b><span>min</span></div>"
        f"<div><b>{view.words:,}</b><span>{words_label}</span></div>"
        f"<div><b>{lane.words_total:,}</b><span>total</span></div>"
        f"</div></div>"
    )


def _render_meter(meter: Meter) -> str:
    percent = meter.percent
    level = "bad" if percent > BAD_PERCENT else "warn" if percent > WARN_PERCENT else ""
    if meter.unit == "cores":
        detail = f"{meter.used:.2f} of {meter.total:.0f} cores (5 min)"
    else:
        detail = f"{meter.used:,.1f} of {meter.total:,.1f} {meter.unit}"
    return (
        f'<div class="card meter {level}">'
        f'<div class="top"><span class="name">{_esc(meter.label)}</span>'
        f'<span class="pct">{percent:.0f}%</span></div>'
        f'<div class="bar"><div class="fill" style="width:{percent:.1f}%"></div></div>'
        f'<div class="detail">{_esc(detail)}</div>'
        f"</div>"
    )


def _render_period(dashboard: Dashboard, period: str) -> str:
    """The lanes of one period, with its ruler on top."""
    now = dashboard.now
    lanes = dashboard.lanes
    if not lanes:
        return '<div class="empty">No contributors yet.</div>'
    if period in TIMELINE_SPANS:
        span = TIMELINE_SPANS[period]
        window_start = now - span
        ticks = tick_times(window_start, now, TICK_HOURS if period == "day" else 24)
        ruler = _timeline_ruler(period, window_start, ticks)
        tracks = [
            _render_timeline(lane.views[period].blocks, window_start, span, ticks)
            for lane in lanes
        ]
    else:
        ruler = _bars_ruler([bar.bucket for bar in lanes[0].views[period].bars])
        # One scale for every lane, so bar heights compare across people.
        top = max(
            [1] + [bar.minutes for lane in lanes for bar in lane.views[period].bars]
        )
        tracks = [_render_bars(lane.views[period].bars, top) for lane in lanes]
    has_real = any(not lane.is_test for lane in lanes)
    rows: list[str] = [
        '<div class="row ruler"><div class="who"></div>'
        f'<div class="hours">{ruler}</div>'
        '<div class="stats"></div></div>'
    ]
    seen_test = False
    for lane, track in zip(lanes, tracks, strict=True):
        first_test = lane.is_test and not seen_test and has_real
        seen_test = seen_test or lane.is_test
        rows.append(_render_lane(lane, period, first_test, track, now))
    return "".join(rows)


def _view_css() -> str:
    shown = ",\n".join(
        f"body[data-view={p}] .view[data-view={p}], body[data-view={p}] [data-for={p}]"
        for p in PERIODS
    )
    return f"{shown} {{ display: block; }}\n"


VIEW_SCRIPT = """<script>
// The chosen period survives the once-a-minute reload.
const VIEWS = ["day", "week", "month", "year", "all"];
let chosen = null;
try { chosen = localStorage.getItem("dpd-dashboard-view"); } catch (e) {}
function show(view) {
  if (!VIEWS.includes(view)) view = "day";
  document.body.dataset.view = view;
  document.querySelectorAll(".views button").forEach(
    (b) => b.setAttribute("aria-pressed", String(b.dataset.view === view)));
  try { localStorage.setItem("dpd-dashboard-view", view); } catch (e) {}
}
document.querySelectorAll(".views button").forEach(
  (b) => b.addEventListener("click", () => show(b.dataset.view)));
show(chosen);
</script>"""


def render_page(dashboard: Dashboard, css_variables: str) -> str:
    now = dashboard.now
    real_lanes = [lane for lane in dashboard.lanes if not lane.is_test]
    online = sum(
        lane.state in (State.ONLINE, State.SLEEPING_SOON) for lane in real_lanes
    )
    online_css = "online" if online else ""
    test_note = f"test users ({', '.join(dashboard.test_users)}) not counted"

    total_note = "none yet"
    if dashboard.first_day:
        first = date.fromisoformat(dashboard.first_day)
        total_note = f"since {first.day} {first:%b %Y}"
    values: list[str] = []
    labels: list[str] = []
    notes: list[str] = []
    for period in PERIODS:
        start = dashboard.period_starts[period]
        values.append(
            f'<div class="value" data-for="{period}">{dashboard.period_words[period]:,}</div>'
        )
        label = (
            "words added today"
            if period == "day"
            else f"words added, {PERIOD_NAMES[period]}"
        )
        labels.append(f'<div class="label" data-for="{period}">{label}</div>')
        if period == "day":
            when = f"{now:%A %d %B}"
        elif period == "all":
            # The first day with words, as under the total, not the 1st of
            # that month the All bars start from.
            when = total_note
        else:
            when = f"since {start.day} {start:%b %Y}"
        notes.append(
            f'<div class="note" data-for="{period}">{_esc(when)} · {_esc(test_note)}</div>'
        )
    buttons = "".join(
        f'<button type="button" data-view="{p}" aria-pressed="{str(p == "day").lower()}">{p.title()}</button>'
        for p in PERIODS
    )
    sections = "".join(
        f'<section class="card lanes view" data-view="{p}">{_render_period(dashboard, p)}</section>'
        for p in PERIODS
    )
    meters_html = "".join(_render_meter(meter) for meter in dashboard.meters)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="{RELOAD_SECONDS}">
<title>Contributor dashboard</title>
<link rel="icon" href="{LOGO_NAME}">
<style>
{css_variables}
{PAGE_CSS}
{_view_css()}
</style>
</head>
<body data-view="day">
<main>
<header>
  <img src="{LOGO_NAME}" alt="DPD">
  <div>
    <h1>Contributor dashboard</h1>
    <div class="sub">Updated {now.strftime("%a %d %b %Y, %H:%M")} server time · reloads every minute</div>
  </div>
  <div class="presence {online_css}"><span class="dot"></span>{online} of {len(real_lanes)} online</div>
</header>

<section class="numbers">
  <div class="card number">
    {"".join(values)}
    {"".join(labels)}
    {"".join(notes)}
  </div>
  <div class="card number">
    <div class="value">{dashboard.words_total:,}</div>
    <div class="label">words added in total</div>
    <div class="note">{_esc(total_note)}</div>
  </div>
</section>

<div class="section-title">Server</div>
<section class="meters">{meters_html}</section>

<div class="section-head">
  <div class="section-title">Contributors</div>
  <div class="views">{buttons}</div>
</div>
{sections}
</main>
{VIEW_SCRIPT}
</body>
</html>
"""


def write_page(out_dir: Path, page: str, project_root: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for source, name in ((LOGO_SOURCE, LOGO_NAME), (FONT_SOURCE, FONT_NAME)):
        target = out_dir / name
        if not target.exists():
            shutil.copyfile(project_root / source, target)
    # Write then swap, so nginx never serves half a page. The pid keeps two
    # overlapping cron runs off each other's temp file.
    tmp = out_dir / f"index.html.{os.getpid()}.tmp"
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(out_dir / "index.html")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--data-dir", type=Path, default=Path("/var/lib/dpd/contrib_data")
    )
    parser.add_argument("--env-dir", type=Path, default=Path("/etc/dpd"))
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--test-user", action="append", default=None)
    parser.add_argument(
        "--seconds-file", type=Path, default=Path("/var/lib/dpd/dashboard_seconds.json")
    )
    args = parser.parse_args()

    now = datetime.now().astimezone()
    tz = now.tzinfo if now.tzinfo is not None else UTC
    test_users: set[str] = set(
        args.test_user if args.test_user is not None else TEST_USERS
    )

    users = read_users(args.env_dir)
    # From midnight, so the oldest day read is a whole day.
    since = datetime.combine(now.date() - timedelta(days=HISTORY_DAYS), time(), tz)
    lines = read_journal(since)
    visits = build_visits(parse_journal(lines, tz))
    seconds = merge_seconds(
        read_seconds(args.seconds_file),
        seconds_per_day(visits, now),
        now,
        journal_start(lines, tz),
    )
    # A failed save must not stop the page: the next run tries again.
    try:
        write_seconds(args.seconds_file, seconds)
    except OSError as exc:
        print(f"could not save {args.seconds_file}: {exc}")
    words = read_daily_logs(args.data_dir)
    lanes = build_lanes(
        users,
        read_units(users),
        visits,
        words,
        seconds,
        test_users,
        now,
        read_added(args.env_dir, users, tz),
    )
    dashboard = build_dashboard(lanes, read_meters(), words, seconds, test_users, now)
    css_variables = (args.project_root / CSS_VARIABLES_SOURCE).read_text(
        encoding="utf-8"
    )
    write_page(args.out_dir, render_page(dashboard, css_variables), args.project_root)


if __name__ == "__main__":
    main()
