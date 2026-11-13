"""The contributor dashboard: journal lines → visits → lanes → page.

The fixture is real `journalctl -o json` output of the test users' units
(bdhrs, deva), cut to the fields the parser reads.
"""

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.server_contrib import contrib_dashboard
from scripts.server_contrib.contrib_dashboard import (
    Dashboard,
    Event,
    Kind,
    Lane,
    Meter,
    State,
    Unit,
    Visit,
    blocks_for_day,
    build_dashboard,
    build_lanes,
    build_visits,
    lane_state,
    parse_daily_log,
    parse_journal,
    parse_systemctl_show,
    read_journal,
    render_page,
)

SERVER_TZ = timezone(timedelta(hours=5, minutes=30))
FIXTURE = Path("tests/scripts/server_contrib/data/dashboard_journal.jsonl")


def _fixture_events() -> list[Event]:
    return parse_journal(FIXTURE.read_text(encoding="utf-8").splitlines(), SERVER_TZ)


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=SERVER_TZ)


def _line(at: datetime, message: object, unit: str = "dpd-gui@alice.service") -> str:
    stamp = str(int(at.timestamp() * 1_000_000))
    if isinstance(message, str) and message.startswith(("Started ", "Stopped ")):
        record = {
            "__REALTIME_TIMESTAMP": stamp,
            "MESSAGE": message,
            "_SYSTEMD_UNIT": "init.scope",
            "UNIT": unit,
        }
    else:
        record = {
            "__REALTIME_TIMESTAMP": stamp,
            "MESSAGE": message,
            "_SYSTEMD_UNIT": unit,
        }
    return json.dumps(record)


def _visits_of(user: str) -> list[Visit]:
    return [visit for visit in build_visits(_fixture_events()) if visit.user == user]


def _second(at: datetime | None) -> datetime | None:
    # Real journal times carry microseconds; the tests name whole seconds.
    return at.replace(microsecond=0) if at else None


def test_fixture_holds_every_line_kind() -> None:
    kinds = {event.kind for event in _fixture_events()}
    assert kinds == {
        Kind.CONNECT,
        Kind.COUNTDOWN,
        Kind.ASLEEP,
        Kind.STOPPED,
        Kind.STARTED,
    }


def test_systemd_lines_are_read_from_the_unit_field() -> None:
    started = [event for event in _fixture_events() if event.kind is Kind.STARTED]
    assert {event.user for event in started} == {"bdhrs", "deva"}


def test_asleep_ends_the_visit_at_the_last_action() -> None:
    # 16:20:27 "asleep: 32.1 min idle": the last action was at 15:48:21.
    visit = next(
        v for v in _visits_of("bdhrs") if _second(v.start) == _at("2026-11-12T15:19:12")
    )
    assert _second(visit.end) == _at("2026-11-12T15:48:21")


def test_a_stop_ends_the_visit() -> None:
    visit = next(
        v for v in _visits_of("bdhrs") if _second(v.start) == _at("2026-11-12T15:08:52")
    )
    assert _second(visit.end) == _at("2026-11-12T15:19:07")


def test_a_second_page_in_the_same_editor_is_the_same_visit() -> None:
    # 15:24:53 and 15:26:47 both say "page connected"; sleep came at 16:03:23.
    starts = [_second(v.start) for v in _visits_of("bdhrs")]
    assert _at("2026-11-11T15:24:53") in starts
    assert _at("2026-11-11T15:26:47") not in starts


def test_no_visit_in_the_fixture_is_negative_or_left_open() -> None:
    visits = build_visits(_fixture_events())
    assert len(visits) == 13
    for visit in visits:
        assert visit.end is not None
        assert visit.end >= visit.start


def test_reconnect_starts_a_visit_and_restart_ends_it() -> None:
    lines = [
        _line(_at("2026-11-13T09:00:00"), "lifecycle: page reconnected"),
        _line(_at("2026-11-13T09:20:00"), "Started dpd-gui@alice.service - DPD gui2"),
    ]
    visits = build_visits(parse_journal(lines, SERVER_TZ))
    assert [(v.start, v.end) for v in visits] == [
        (_at("2026-11-13T09:00:00"), _at("2026-11-13T09:20:00"))
    ]


def test_countdown_and_cancel_set_the_lane_state() -> None:
    unit = Unit("alice", active=True, memory_bytes=800 * 1024**2)
    lines = [
        _line(_at("2026-11-13T09:00:00"), "lifecycle: page connected"),
        _line(
            _at("2026-11-13T09:30:00"), "lifecycle: countdown shown after 30.0 min idle"
        ),
    ]
    visit = build_visits(parse_journal(lines, SERVER_TZ))[0]
    assert lane_state(unit, visit) is State.SLEEPING_SOON

    lines.append(_line(_at("2026-11-13T09:31:00"), "lifecycle: countdown cancelled"))
    visit = build_visits(parse_journal(lines, SERVER_TZ))[0]
    assert lane_state(unit, visit) is State.ONLINE


def test_lane_state_without_a_page_or_a_unit() -> None:
    assert lane_state(Unit("alice", True, None), None) is State.ASLEEP
    assert lane_state(Unit("alice", False, None), None) is State.DOWN
    assert lane_state(None, None) is State.DOWN


def test_other_lines_and_byte_messages_are_skipped() -> None:
    lines = [
        _line(_at("2026-11-13T09:00:00"), "lifecycle: notice file: absent"),
        _line(_at("2026-11-13T09:00:01"), [104, 105]),
        _line(
            _at("2026-11-13T09:00:02"), "lifecycle: page connected", unit="sshd.service"
        ),
        "not json",
        "",
    ]
    assert parse_journal(lines, SERVER_TZ) == []


def test_blocks_are_cut_to_today_and_an_open_visit_runs_to_now() -> None:
    day_start = _at("2026-11-13T00:00:00")
    now = _at("2026-11-13T10:00:00")
    visits = [
        Visit("alice", _at("2026-11-12T23:40:00"), _at("2026-11-13T00:20:00")),
        Visit("alice", _at("2026-11-12T20:00:00"), _at("2026-11-12T21:00:00")),
        Visit("alice", _at("2026-11-13T09:15:00")),
    ]
    blocks = blocks_for_day(visits, day_start, now)
    assert [(b.start, b.end, b.is_open) for b in blocks] == [
        (day_start, _at("2026-11-13T00:20:00"), False),
        (_at("2026-11-13T09:15:00"), now, True),
    ]


def test_lanes_put_test_users_last_and_count_words_and_minutes() -> None:
    now = _at("2026-11-13T10:00:00")
    units = {user: Unit(user, True, 77 * 1024**2) for user in ("bdhrs", "zed", "alice")}
    visits = [
        Visit("alice", _at("2026-11-13T08:00:00"), _at("2026-11-13T08:45:00")),
        Visit("alice", _at("2026-11-13T09:30:00")),
    ]
    words = {"alice": {"2026-11-12": 5, "2026-11-13": 3}, "bdhrs": {"2026-11-13": 7}}
    lanes = build_lanes(["bdhrs", "zed", "alice"], units, visits, words, {"bdhrs"}, now)

    assert [lane.user for lane in lanes] == ["alice", "zed", "bdhrs"]
    alice = lanes[0]
    assert alice.state is State.ONLINE
    assert alice.minutes_today == 75
    assert (alice.words_today, alice.words_total) == (3, 8)
    assert alice.online_since == _at("2026-11-13T09:30:00")
    assert alice.last_seen == _at("2026-11-13T08:45:00")
    assert lanes[1].state is State.ASLEEP
    assert lanes[2].is_test


def test_big_numbers_leave_out_test_users() -> None:
    now = _at("2026-11-13T10:00:00")
    words = {
        "alice": {"2026-11-10": 4, "2026-11-13": 3},
        "gone": {"2026-11-13": 2},
        "bdhrs": {"2026-11-01": 50, "2026-11-13": 9},
    }
    dashboard = build_dashboard([], [], words, {"bdhrs"}, now)
    assert (dashboard.words_today, dashboard.words_total) == (5, 9)
    assert dashboard.first_day == "2026-11-10"


def test_daily_log_adds_every_counter() -> None:
    text = json.dumps(
        {"2026-11-13": {"pass1": 4, "pass2_pre": 2}, "2026-11-12": {"pass1": 1}}
    )
    assert parse_daily_log(text) == {"2026-11-13": 6, "2026-11-12": 1}


def test_systemctl_show_blocks() -> None:
    text = (
        "Id=dpd-gui@alice.service\nActiveState=active\nMemoryCurrent=812000000\n\n"
        "Id=dpd-gui@bob.service\nActiveState=inactive\nMemoryCurrent=[not set]\n"
    )
    units = parse_systemctl_show(text)
    assert units["alice"] == Unit("alice", True, 812000000)
    assert units["bob"] == Unit("bob", False, None)


def test_meter_percent_is_capped() -> None:
    assert Meter("CPU load", 3.0, 2, "cores").percent == 100.0
    assert Meter("Swap", 0.0, 0.0, "GB").percent == 0.0


def test_page_shows_lanes_numbers_and_meters() -> None:
    now = _at("2026-11-13T10:00:00")
    lane = Lane(
        user="alice",
        state=State.ONLINE,
        blocks=[],
        minutes_today=12,
        words_today=3,
        words_total=1234,
        memory_bytes=800 * 1024**2,
        is_test=False,
        online_since=_at("2026-11-13T09:48:00"),
        last_seen=None,
    )
    dashboard = Dashboard(
        now=now,
        lanes=[lane],
        meters=[Meter("Disk", 95.0, 100.0, "GB")],
        words_today=3,
        words_total=1234,
        first_day="2026-11-13",
        test_users=["bdhrs"],
    )
    page = render_page(dashboard, ":root { --primary: blue; }")
    assert "1,234" in page
    assert "online since 09:48" in page
    assert "1 of 1 online" in page
    assert 'class="card meter bad"' in page
    assert ":root { --primary: blue; }" in page


def test_a_dying_process_ends_the_visit_without_a_restart() -> None:
    # A unit that hits its start limit stays failed and never logs Started.
    lines = [
        _line(_at("2026-11-13T09:00:00"), "lifecycle: page connected"),
        _line(
            _at("2026-11-13T09:40:00"),
            "dpd-gui@alice.service: Main process exited, code=killed, status=9/KILL",
            unit="init.scope",
        ),
    ]
    records = [json.loads(line) for line in lines]
    records[1]["UNIT"] = "dpd-gui@alice.service"
    visits = build_visits(parse_journal([json.dumps(r) for r in records], SERVER_TZ))
    assert [(v.start, v.end) for v in visits] == [
        (_at("2026-11-13T09:00:00"), _at("2026-11-13T09:40:00"))
    ]


def test_auto_restart_after_sleep_is_not_down() -> None:
    units = parse_systemctl_show(
        "Id=dpd-gui@alice.service\nActiveState=activating\nMemoryCurrent=[not set]\n"
    )
    assert lane_state(units["alice"], None) is State.ASLEEP


def test_journal_failure_still_gives_a_page(monkeypatch) -> None:
    # journalctl on systemd 255 exits 1 when no unit matches the pattern yet.
    def fake_run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        result = subprocess.CompletedProcess(
            args, 1, stdout="", stderr="No data available"
        )
        if kwargs.get("check"):
            result.check_returncode()
        return result

    monkeypatch.setattr(contrib_dashboard.subprocess, "run", fake_run)
    assert read_journal(_at("2026-11-13T00:00:00")) == []


def _lane(
    user: str, state: State, is_test: bool = False, last_seen: datetime | None = None
) -> Lane:
    return Lane(
        user=user,
        state=state,
        blocks=[],
        minutes_today=0,
        words_today=0,
        words_total=0,
        memory_bytes=None,
        is_test=is_test,
        online_since=_at("2026-11-13T09:00:00") if state is State.ONLINE else None,
        last_seen=last_seen,
    )


def test_page_says_when_an_asleep_lane_was_last_seen() -> None:
    now = _at("2026-11-13T10:00:00")
    lanes = [
        _lane("alice", State.ASLEEP, last_seen=_at("2026-11-12T16:20:00")),
        _lane("bob", State.ASLEEP, last_seen=_at("2026-11-09T08:00:00")),
        _lane("carol", State.ASLEEP),
    ]
    page = render_page(Dashboard(now, lanes, [], 0, 0, None), "")
    assert "asleep, last seen yesterday 16:20" in page
    assert "asleep, last seen 9 Nov" in page
    assert "asleep, not seen in 14 days" in page


def test_test_users_do_not_count_as_online() -> None:
    now = _at("2026-11-13T10:00:00")
    lanes = [_lane("alice", State.ASLEEP), _lane("bdhrs", State.ONLINE, is_test=True)]
    page = render_page(Dashboard(now, lanes, [], 0, 0, None), "")
    assert "0 of 1 online" in page
