"""Write the contributor dashboard: who is in the editor, when each contributor
was online today, how many words they added, and how full the server is.

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
from datetime import UTC, datetime, time, timedelta, tzinfo
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
class Lane:
    user: str
    state: State
    blocks: list[Block]
    minutes_today: int
    words_today: int
    words_total: int
    memory_bytes: int | None
    is_test: bool
    online_since: datetime | None
    last_seen: datetime | None


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
    words_today: int
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


def blocks_for_day(
    visits: Iterable[Visit], day_start: datetime, now: datetime
) -> list[Block]:
    """The visits cut to the part between day_start and now."""
    blocks: list[Block] = []
    for visit in visits:
        end = now if visit.end is None else min(visit.end, now)
        start = max(visit.start, day_start)
        if end < start or (visit.end is not None and end <= day_start):
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


def build_lanes(
    users: list[str],
    units: dict[str, Unit],
    visits: list[Visit],
    words: dict[str, dict[str, int]],
    test_users: set[str],
    now: datetime,
) -> list[Lane]:
    """One lane per user: real contributors first, test users last, each group
    by name, so a lane never moves between reloads."""
    day_start = datetime.combine(now.date(), time(), now.tzinfo)
    today = now.date().isoformat()
    lanes: list[Lane] = []
    for user in sorted(users, key=lambda name: (name in test_users, name)):
        own = [visit for visit in visits if visit.user == user]
        open_visit = next((visit for visit in own if visit.end is None), None)
        unit = units.get(user)
        state = lane_state(unit, open_visit)
        blocks = blocks_for_day(own, day_start, now)
        seconds = sum((block.end - block.start).total_seconds() for block in blocks)
        ended = [visit.end for visit in own if visit.end is not None]
        per_day = words.get(user, {})
        lanes.append(
            Lane(
                user=user,
                state=state,
                blocks=blocks,
                minutes_today=round(seconds / 60),
                words_today=per_day.get(today, 0),
                words_total=sum(per_day.values()),
                memory_bytes=unit.memory_bytes if unit else None,
                is_test=user in test_users,
                online_since=open_visit.start if open_visit else None,
                last_seen=max(ended) if ended else None,
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
    test_users: set[str],
    now: datetime,
) -> Dashboard:
    """The big numbers count real contributors only, including any who no
    longer have a lane."""
    today = now.date().isoformat()
    real = {user: days for user, days in words.items() if user not in test_users}
    days_with_words = sorted(
        day for days in real.values() for day, count in days.items() if count
    )
    return Dashboard(
        now=now,
        lanes=lanes,
        meters=meters,
        words_today=sum(days.get(today, 0) for days in real.values()),
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
  background:
    repeating-linear-gradient(90deg, var(--tick) 0 1px, transparent 1px 12.5%),
    var(--track);
}
.block {
  position: absolute;
  top: 6px; bottom: 6px;
  border-radius: 5px;
  background: var(--primary);
}
.block.open { background: var(--ok); box-shadow: 0 0 12px hsla(150, 80%, 45%, 0.55); }
.now {
  position: absolute;
  top: -4px; bottom: -4px;
  width: 2px;
  margin-left: -1px;
  background: var(--text);
  opacity: 0.55;
  border-radius: 2px;
}
.hours { position: relative; height: 16px; font-size: 11px; color: var(--muted); }
.hours span { position: absolute; transform: translateX(-50%); font-variant-numeric: tabular-nums; }
.hours span:first-child { transform: none; }
.hours span:last-child { transform: translateX(-100%); }

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


def _megabytes(value: int | None) -> str:
    if value is None:
        return ""
    return f"{value / 1024**2:,.0f} MB"


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
    else:
        text = f"asleep, not seen in {HISTORY_DAYS} days"
    return f"{text} · {memory}" if memory and lane.state is not State.DOWN else text


def _percent_of_day(at: datetime, day_start: datetime) -> float:
    return 100.0 * (at - day_start).total_seconds() / 86400


def _render_track(lane: Lane, day_start: datetime, now: datetime) -> str:
    parts: list[str] = []
    for block in lane.blocks:
        left = _percent_of_day(block.start, day_start)
        width = max(MIN_BLOCK_PERCENT, _percent_of_day(block.end, day_start) - left)
        minutes = round((block.end - block.start).total_seconds() / 60)
        end_text = "now" if block.is_open else _clock(block.end)
        title = f"{_clock(block.start)} – {end_text} · {minutes} min"
        css = "block open" if block.is_open else "block"
        parts.append(
            f'<div class="{css}" style="left:{left:.3f}%;width:{width:.3f}%" '
            f'title="{_esc(title)}"></div>'
        )
    parts.append(
        f'<div class="now" style="left:{_percent_of_day(now, day_start):.3f}%"></div>'
    )
    return f'<div class="track">{"".join(parts)}</div>'


def _render_lane(
    lane: Lane, first_test: bool, day_start: datetime, now: datetime
) -> str:
    state_css = lane.state.name.lower().replace("_", "-")
    classes = f"row {state_css}" + (" test-first" if first_test else "")
    tag = '<span class="tag">test</span>' if lane.is_test else ""
    return (
        f'<div class="{classes}">'
        f'<div class="who"><span class="dot"></span><div>'
        f'<div class="name">{_esc(lane.user)}{tag}</div>'
        f'<div class="state">{_esc(_state_text(lane, now))}</div>'
        f"</div></div>"
        f"{_render_track(lane, day_start, now)}"
        f'<div class="stats">'
        f"<div><b>{lane.minutes_today:,}</b><span>min</span></div>"
        f"<div><b>{lane.words_today:,}</b><span>today</span></div>"
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


def render_page(dashboard: Dashboard, css_variables: str) -> str:
    now = dashboard.now
    day_start = datetime.combine(now.date(), time(), now.tzinfo)
    real_lanes = [lane for lane in dashboard.lanes if not lane.is_test]
    online = sum(
        lane.state in (State.ONLINE, State.SLEEPING_SOON) for lane in real_lanes
    )
    online_css = "online" if online else ""

    rows: list[str] = []
    seen_test = False
    for lane in dashboard.lanes:
        first_test = lane.is_test and not seen_test and bool(real_lanes)
        seen_test = seen_test or lane.is_test
        rows.append(_render_lane(lane, first_test, day_start, now))
    hours = "".join(
        f'<span style="left:{hour / 24 * 100:.3f}%">{hour:02d}</span>'
        for hour in range(0, 25, 3)
    )
    ruler = (
        '<div class="row ruler"><div class="who"></div>'
        f'<div class="hours">{hours}</div>'
        '<div class="stats"><div></div><div></div><div></div></div></div>'
    )
    lanes_html = (
        ruler + "".join(rows)
        if rows
        else '<div class="empty">No contributors yet.</div>'
    )

    test_note = ", ".join(dashboard.test_users)
    total_note = f"since {dashboard.first_day}" if dashboard.first_day else "none yet"
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
</style>
</head>
<body>
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
    <div class="value">{dashboard.words_today:,}</div>
    <div class="label">words added today</div>
    <div class="note">{now.strftime("%A %d %B")} · test users ({_esc(test_note)}) not counted</div>
  </div>
  <div class="card number">
    <div class="value">{dashboard.words_total:,}</div>
    <div class="label">words added in total</div>
    <div class="note">{_esc(total_note)}</div>
  </div>
</section>

<div class="section-title">Server</div>
<section class="meters">{meters_html}</section>

<div class="section-title">Contributors today</div>
<section class="card lanes">{lanes_html}</section>
</main>
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
    args = parser.parse_args()

    now = datetime.now().astimezone()
    tz = now.tzinfo if now.tzinfo is not None else UTC
    test_users: set[str] = set(
        args.test_user if args.test_user is not None else TEST_USERS
    )

    users = read_users(args.env_dir)
    events = parse_journal(read_journal(now - timedelta(days=HISTORY_DAYS)), tz)
    words = read_daily_logs(args.data_dir)
    lanes = build_lanes(
        users, read_units(users), build_visits(events), words, test_users, now
    )
    dashboard = build_dashboard(lanes, read_meters(), words, test_users, now)
    css_variables = (args.project_root / CSS_VARIABLES_SOURCE).read_text(
        encoding="utf-8"
    )
    write_page(args.out_dir, render_page(dashboard, css_variables), args.project_root)


if __name__ == "__main__":
    main()
