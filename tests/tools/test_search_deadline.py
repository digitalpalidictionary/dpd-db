import time
from types import SimpleNamespace

import pytest

import tools.search_deadline as sd
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tools.search_deadline import (
    SearchTimeout,
    current_deadline,
    raise_if_stopped,
    regex_deadline,
    regexp_search,
    sub,
)

# Python's re hangs on this; the regex package gives up at the timeout.
SLOW_PATTERN = r"^(a|a)+$"
SLOW_TEXT = "a" * 60 + "b"


def test_without_deadline_uses_plain_re() -> None:
    assert regexp_search("dham+a", "dhamma") is True
    assert regexp_search("dham+a", "DHAMMA") is False
    assert regexp_search("zzz", "dhamma") is False
    assert regexp_search("a", None) is None
    assert sub("(a)", r"<\g<1>>", "banana") == "b<a>n<a>n<a>"


def test_inside_deadline_matches_like_normal() -> None:
    with regex_deadline(5):
        assert regexp_search("dham+a", "dhamma") is True
        assert regexp_search("dham+a", "DHAMMA") is False
        assert regexp_search("zzz", "dhamma") is False
        assert sub("(a)", r"<\g<1>>", "banana") == "b<a>n<a>n<a>"


def test_slow_pattern_stops_at_budget() -> None:
    start = time.monotonic()
    with regex_deadline(0.3) as deadline:
        with pytest.raises(SearchTimeout):
            regexp_search(SLOW_PATTERN, SLOW_TEXT)
        assert isinstance(deadline.stopped, SearchTimeout)
        with pytest.raises(SearchTimeout):
            raise_if_stopped()
    assert time.monotonic() - start < 2


def test_slow_substitution_stops_at_budget() -> None:
    with regex_deadline(0.3):
        with pytest.raises(SearchTimeout):
            sub(f"({SLOW_PATTERN})", r"<\g<1>>", SLOW_TEXT)


def test_spent_budget_stops_the_next_call() -> None:
    with regex_deadline(0):
        with pytest.raises(SearchTimeout):
            regexp_search("a", "a")


def test_deadline_does_not_leak_out_of_the_block() -> None:
    with regex_deadline(0.3):
        pass
    assert current_deadline() is None
    raise_if_stopped()


def test_deadline_is_set_inside_a_sync_route_and_not_left_behind() -> None:
    app = FastAPI()

    @app.get("/probe")
    def probe() -> dict[str, bool]:
        with regex_deadline(5):
            return {"set": current_deadline() is not None}

    @app.get("/outside")
    def outside() -> dict[str, bool]:
        return {"set": current_deadline() is not None}

    client = TestClient(app)
    assert client.get("/probe").json() == {"set": True}
    assert client.get("/outside").json() == {"set": False}


@pytest.fixture
def fake_clock(monkeypatch: pytest.MonkeyPatch) -> dict[str, float]:
    clock = {"cpu": 100.0, "wall": 1000.0}
    monkeypatch.setattr(
        sd,
        "time",
        SimpleNamespace(
            thread_time=lambda: clock["cpu"], monotonic=lambda: clock["wall"]
        ),
    )
    return clock


def test_budget_counts_the_searchs_own_cpu_time_not_waiting(
    fake_clock: dict[str, float],
) -> None:
    """Searches take turns on Python's global lock, so four ordinary searches at
    once each wait about three times as long as they work. Waiting must not
    use up the budget."""
    with sd.regex_deadline(4) as deadline:
        fake_clock["wall"] += 15
        assert deadline.remaining() > 0
        fake_clock["cpu"] += 4.1
        with pytest.raises(SearchTimeout):
            deadline.remaining()


def test_wall_clock_is_only_a_backstop(fake_clock: dict[str, float]) -> None:
    with sd.regex_deadline(4) as deadline:
        fake_clock["wall"] += 21
        with pytest.raises(SearchTimeout):
            deadline.remaining()
