"""The contributor dashboard: journal lines → visits → lanes → page.

The fixture is real `journalctl -o json` output of the test users' units
(bdhrs, deva), cut to the fields the parser reads.
"""

import json
import subprocess
from dataclasses import replace
from datetime import date
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.server_contrib import contrib_dashboard
from scripts.server_contrib.contrib_dashboard import (
    Event,
    Kind,
    Lane,
    Meter,
    State,
    Unit,
    Visit,
    blocks_in_window,
    busy_percent,
    bar_buckets,
    build_dashboard,
    build_lanes,
    build_visits,
    journal_start,
    lane_state,
    merge_seconds,
    seconds_per_day,
    parse_daily_log,
    parse_journal,
    parse_systemctl_show,
    read_journal,
    read_cpu_meter,
    read_seconds,
    render_page,
    tick_times,
    write_seconds,
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


def test_blocks_are_cut_to_the_window_and_an_open_visit_runs_to_now() -> None:
    window_start = _at("2026-11-12T10:00:00")
    now = _at("2026-11-13T10:00:00")
    visits = [
        Visit("alice", _at("2026-11-12T08:00:00"), _at("2026-11-12T09:00:00")),
        Visit("alice", _at("2026-11-12T09:00:00"), _at("2026-11-12T11:00:00")),
        Visit("alice", _at("2026-11-12T20:00:00"), _at("2026-11-12T21:00:00")),
        Visit("alice", _at("2026-11-13T09:15:00")),
    ]
    blocks = blocks_in_window(visits, window_start, now)
    assert [(b.start, b.end, b.is_open) for b in blocks] == [
        (window_start, _at("2026-11-12T11:00:00"), False),
        (_at("2026-11-12T20:00:00"), _at("2026-11-12T21:00:00"), False),
        (_at("2026-11-13T09:15:00"), now, True),
    ]


def test_lane_counts_yesterday_evening_inside_the_last_24_hours() -> None:
    now = _at("2026-11-13T10:00:00")
    visits = [Visit("alice", _at("2026-11-12T20:00:00"), _at("2026-11-12T21:00:00"))]
    lanes = build_lanes(
        ["alice"], {"alice": Unit("alice", True, None)}, visits, {}, {}, set(), now
    )
    assert lanes[0].views["day"].minutes == 60


def test_ticks_sit_on_clock_hours_with_midnight_inside() -> None:
    ticks = tick_times(_at("2026-11-12T14:20:00"), _at("2026-11-13T14:20:00"))
    assert [t.strftime("%d %H") for t in ticks] == [
        "12 15",
        "12 18",
        "12 21",
        "13 00",
        "13 03",
        "13 06",
        "13 09",
        "13 12",
    ]


def test_lanes_put_test_users_last_and_count_words_and_minutes() -> None:
    now = _at("2026-11-13T10:00:00")
    units = {user: Unit(user, True, 77 * 1024**2) for user in ("bdhrs", "zed", "alice")}
    visits = [
        Visit("alice", _at("2026-11-13T08:00:00"), _at("2026-11-13T08:45:00")),
        Visit("alice", _at("2026-11-13T09:30:00")),
    ]
    words = {"alice": {"2026-11-12": 5, "2026-11-13": 3}, "bdhrs": {"2026-11-13": 7}}
    lanes = build_lanes(
        ["bdhrs", "zed", "alice"], units, visits, words, {}, {"bdhrs"}, now
    )

    assert [lane.user for lane in lanes] == ["alice", "zed", "bdhrs"]
    alice = lanes[0]
    assert alice.state is State.ONLINE
    assert alice.views["day"].minutes == 75
    assert (alice.views["day"].words, alice.words_total) == (3, 8)
    assert alice.views["week"].words == 8
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
    dashboard = build_dashboard([], [], words, {}, {"bdhrs"}, now)
    assert (dashboard.period_words["day"], dashboard.words_total) == (5, 9)
    assert dashboard.period_words["week"] == 9
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
    lane = _lane(
        "alice",
        State.ONLINE,
        now=now,
        words_total=1234,
        memory_bytes=800 * 1024**2,
        online_since=_at("2026-11-13T09:48:00"),
    )
    page = render_page(
        build_dashboard([lane], [Meter("Disk", 95.0, 100.0, "GB")], {}, {}, set(), now),
        ":root { --primary: blue; }",
    )
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
    user: str,
    state: State,
    is_test: bool = False,
    last_seen: datetime | None = None,
    now: datetime = _at("2026-11-13T10:00:00"),
    *,
    online_since: datetime | None = None,
    added: datetime | None = None,
    memory_bytes: int | None = None,
    words_total: int = 0,
) -> Lane:
    """A lane with empty views for every period, built the way the script
    builds one, then given the state the test needs."""
    base = build_lanes([user], {}, [], {}, {}, set(), now)[0]
    if online_since is None and state is State.ONLINE:
        online_since = _at("2026-11-13T09:00:00")
    return replace(
        base,
        state=state,
        is_test=is_test,
        last_seen=last_seen,
        online_since=online_since,
        added=added,
        memory_bytes=memory_bytes,
        words_total=words_total,
    )


def _page(lanes: list[Lane], now: datetime = _at("2026-11-13T10:00:00")) -> str:
    test_users = {lane.user for lane in lanes if lane.is_test}
    return render_page(build_dashboard(lanes, [], {}, {}, test_users, now), "")


def test_page_says_when_an_asleep_lane_was_last_seen() -> None:
    now = _at("2026-11-13T10:00:00")
    lanes = [
        _lane("alice", State.ASLEEP, last_seen=_at("2026-11-12T16:20:00")),
        _lane("bob", State.ASLEEP, last_seen=_at("2026-11-09T08:00:00")),
        _lane("carol", State.ASLEEP),
    ]
    page = _page(lanes, now)
    assert "asleep, last seen yesterday 16:20" in page
    assert "asleep, last seen 9 Nov" in page
    assert "asleep, not seen in 14 days" in page


def test_test_users_do_not_count_as_online() -> None:
    now = _at("2026-11-13T10:00:00")
    lanes = [_lane("alice", State.ASLEEP), _lane("bdhrs", State.ONLINE, is_test=True)]
    page = _page(lanes, now)
    assert "0 of 1 online" in page


def test_a_new_account_says_when_it_was_added() -> None:
    now = _at("2026-11-13T10:00:00")
    new = _lane("alice", State.ASLEEP, added=_at("2026-11-13T09:00:00"))
    old = _lane("bob", State.ASLEEP, added=_at("2026-10-01T09:00:00"))
    page = _page([new, old], now)
    assert "added today, not seen yet" in page
    assert "asleep, not seen in 14 days" in page


def test_memory_and_its_unit_stay_together() -> None:
    now = _at("2026-11-13T10:00:00")
    lane = _lane("alice", State.ASLEEP, memory_bytes=74 * 1024**2)
    page = _page([lane], now)
    assert "74\u00a0MB" in page


def test_ruler_ends_at_now_and_names_the_day_at_midnight() -> None:
    now = _at("2026-11-13T14:20:00")
    page = _page([_lane("alice", State.ASLEEP, now=now)], now)
    assert '<span class="now-label" style="left:100%">now</span>' in page
    assert '<span class="midnight"' in page and ">Fri</span>" in page


def test_seconds_per_day_splits_at_midnight_and_counts_an_open_visit() -> None:
    now = _at("2026-11-13T10:00:00")
    visits = [
        Visit("alice", _at("2026-11-12T23:30:00"), _at("2026-11-13T00:45:00")),
        Visit("alice", _at("2026-11-13T09:40:00")),
    ]
    assert seconds_per_day(visits, now) == {
        "alice": {"2026-11-12": 30 * 60, "2026-11-13": 65 * 60}
    }


def test_merge_keeps_old_days_and_redoes_the_recent_ones() -> None:
    now = _at("2026-11-13T10:00:00")
    covered_from = _at("2026-10-15T01:00:00")
    stored = {"alice": {"2026-10-01": 40, "2026-11-12": 99}, "bob": {"2026-11-13": 5}}
    fresh = {"alice": {"2026-10-20": 15, "2026-11-12": 30}}
    assert merge_seconds(stored, fresh, now, covered_from) == {
        # 1 Oct is gone from the journal but kept; 20 Oct is new and filled;
        # 12 Nov is recent and counted again; bob's recent day had no visit.
        "alice": {"2026-10-01": 40, "2026-10-20": 15, "2026-11-12": 30},
    }


def test_merge_never_erases_days_the_journal_read_did_not_cover() -> None:
    now = _at("2026-11-13T10:00:00")
    stored = {"alice": {"2026-11-08": 500, "2026-11-12": 99}}
    # The journal now starts on 12 Nov at 09:00: 8 Nov and 12 Nov are not
    # whole days in it, so both keep what was saved; 13 Nov is recounted.
    fresh = {"alice": {"2026-11-12": 20, "2026-11-13": 60}}
    assert merge_seconds(stored, fresh, now, _at("2026-11-12T09:00:00")) == {
        "alice": {"2026-11-08": 500, "2026-11-12": 99, "2026-11-13": 60}
    }
    # A failed or empty read covers nothing: everything saved stays.
    assert merge_seconds(stored, {}, now, None) == stored


def test_journal_start_is_the_first_line_read() -> None:
    lines = ["", "not json", _line(_at("2026-11-01T01:00:00"), "anything")]
    assert journal_start(lines, SERVER_TZ) == _at("2026-11-01T01:00:00")
    assert journal_start([], SERVER_TZ) is None


def test_minutes_file_round_trip_and_damaged_file(tmp_path: Path) -> None:
    path = tmp_path / "dashboard_seconds.json"
    assert read_seconds(path) == {}
    write_seconds(path, {"alice": {"2026-11-13": 12}})
    assert read_seconds(path) == {"alice": {"2026-11-13": 12}}
    path.write_text("{not json", encoding="utf-8")
    assert read_seconds(path) == {}
    path.write_bytes(b"\xff\xfe not text")
    assert read_seconds(path) == {}
    path.write_text("[1, 2]", encoding="utf-8")
    assert read_seconds(path) == {}
    # Every damaged copy is kept; none overwrites another.
    assert len(list(tmp_path.glob("dashboard_seconds.json.corrupt.*"))) == 3
    assert not path.exists()


def test_bar_buckets_for_month_year_and_all() -> None:
    today = date(2026, 11, 13)  # a Friday
    month = bar_buckets("month", today, today)
    assert (len(month), month[0].first, month[-1].last) == (
        30,
        date(2026, 10, 15),
        today,
    )
    year = bar_buckets("year", today, today)
    assert len(year) == 52
    assert year[-1].first == date(2026, 11, 9)  # this week's Monday
    assert year[0].first == date(2025, 11, 17)
    every = bar_buckets("all", today, date(2026, 9, 20))
    assert [b.label for b in every] == ["Sep 26", "Oct 26", "Nov 26"]
    assert every[0].first == date(2026, 9, 1) and every[0].last == date(2026, 9, 30)


def test_bar_views_sum_saved_minutes_and_words_per_bucket() -> None:
    now = _at("2026-11-13T10:00:00")
    seconds = {"alice": {"2026-11-12": 1800, "2026-11-13": 1200, "2026-09-02": 6000}}
    words = {"alice": {"2026-11-13": 4, "2026-09-02": 6}}
    lane = build_lanes(["alice"], {}, [], words, seconds, set(), now)[0]
    month = lane.views["month"]
    assert (month.minutes, month.words) == (50, 4)
    assert [bar.minutes for bar in month.bars][-2:] == [30, 20]
    every = lane.views["all"]
    assert [(bar.bucket.label, bar.minutes) for bar in every.bars] == [
        ("Sep 26", 100),
        ("Oct 26", 0),
        ("Nov 26", 50),
    ]
    assert (every.minutes, every.words) == (150, 10)


def test_page_has_a_toggle_and_one_section_per_period() -> None:
    now = _at("2026-11-13T10:00:00")
    seconds = {"alice": {"2026-11-12": 1800}, "bob": {"2026-11-12": 3600}}
    lanes = build_lanes(["alice", "bob"], {}, [], {}, seconds, set(), now)
    page = render_page(build_dashboard(lanes, [], {}, seconds, set(), now), "")
    assert '<body data-view="day">' in page
    for period in ("day", "week", "month", "year", "all"):
        assert f'<button type="button" data-view="{period}"' in page
        assert f'<section class="card lanes view" data-view="{period}">' in page
        assert f'<div class="value" data-for="{period}">' in page
    # One scale for all lanes: bob's 60 minutes is the full height, alice's half.
    assert 'style="height:100.0%"' in page
    assert 'style="height:50.0%"' in page


def test_a_month_never_counts_less_than_its_week() -> None:
    # Three visits of 40.4 min on three days: rounding each day to a minute
    # would give the month 120 while the week's exact sum is 121.
    now = _at("2026-11-13T10:00:00")
    visits = [
        Visit("alice", _at(f"2026-11-{day}T08:00:00"), _at(f"2026-11-{day}T08:40:24"))
        for day in (10, 11, 12)
    ]
    seconds = seconds_per_day(visits, now)
    lane = build_lanes(["alice"], {}, visits, {}, seconds, set(), now)[0]
    assert lane.views["week"].minutes == lane.views["month"].minutes == 121


def test_a_full_run_keeps_old_history_and_writes_the_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.now().astimezone()
    old_day = (now.date() - timedelta(days=40)).isoformat()
    seconds_file = tmp_path / "dashboard_seconds.json"
    write_seconds(seconds_file, {"alice": {old_day: 6000}})
    env_dir = tmp_path / "env"
    env_dir.mkdir()
    (env_dir / "alice.env").write_text("FLET_SERVER_PORT=8551\n", encoding="utf-8")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "daily_log_alice.json").write_text(
        json.dumps({now.date().isoformat(): {"pass1": 7}}), encoding="utf-8"
    )
    since = now.replace(hour=1, minute=0) - timedelta(days=13)
    lines = [
        _line(since, "Started dpd-gui@alice.service - DPD gui2"),
        _line(now - timedelta(hours=2), "lifecycle: page connected"),
        _line(now - timedelta(hours=1), "Stopped dpd-gui@alice.service - DPD gui2"),
    ]
    monkeypatch.setattr(contrib_dashboard, "read_journal", lambda since: lines)
    monkeypatch.setattr(contrib_dashboard, "read_units", lambda users: {})
    monkeypatch.setattr(contrib_dashboard, "read_meters", lambda cpu_file, now: [])
    out_dir = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        [
            "contrib_dashboard.py",
            "--out-dir",
            str(out_dir),
            "--data-dir",
            str(data_dir),
            "--env-dir",
            str(env_dir),
            "--seconds-file",
            str(seconds_file),
            "--test-user",
            "nobody",
        ],
    )
    contrib_dashboard.main()

    saved = read_seconds(seconds_file)["alice"]
    assert saved[old_day] == 6000
    assert sum(value for day, value in saved.items() if day != old_day) == 3600
    page = (out_dir / "index.html").read_text(encoding="utf-8")
    assert '<div class="value" data-for="day">7</div>' in page
    assert "alice" in page


def test_busy_percent_between_two_readings() -> None:
    before = {"busy": 100.0, "total": 1000.0, "at": 0.0}
    after = {"busy": 112.0, "total": 1120.0, "at": 60.0}
    assert busy_percent(before, after) == 10.0
    assert busy_percent(None, after) is None
    # A reboot resets the counters; an old reading is too stale to use.
    assert busy_percent({"busy": 500.0, "total": 9000.0, "at": 0.0}, after) is None
    assert busy_percent({**before, "at": -1000.0}, after) is None


def test_cpu_meter_shows_busy_share_not_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The live case: load 5.31 on 2 cores while the CPU was mostly idle.
    readings = iter(
        [
            {"busy": 100.0, "total": 1000.0, "at": 0.0},
            {"busy": 106.0, "total": 1120.0, "at": 60.0},
        ]
    )
    monkeypatch.setattr(contrib_dashboard, "cpu_snapshot", lambda at: next(readings))
    monkeypatch.setattr(
        contrib_dashboard.psutil, "getloadavg", lambda: (1.0, 5.31, 4.0)
    )
    monkeypatch.setattr(contrib_dashboard.psutil, "cpu_count", lambda: 2)
    monkeypatch.setattr(contrib_dashboard.psutil, "cpu_percent", lambda interval: 50.0)
    path = tmp_path / "dashboard_cpu.json"
    now = _at("2026-11-13T16:00:00")
    first = read_cpu_meter(path, now)
    assert first.used == 50.0 and "last second" in first.detail
    second = read_cpu_meter(path, now)
    assert second.used == 5.0
    assert second.detail == "busy, since last run · load 5.31 on 2 cores"
    page = render_page(build_dashboard([], [second], {}, {}, set(), now), "")
    assert 'class="card meter "' in page and ">5%</span>" in page
