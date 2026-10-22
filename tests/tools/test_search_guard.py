"""Pattern guard, busy limit and stop handling for webapp regex searches (issue #268)."""

import resource
import subprocess
import sys
import threading
import time

import pytest

import tools.search_deadline as sd
from exporter.webapp.toolkit import fuzzy_replace

# the regex package expands counted repeats: this one needs ~600 MB to compile
BOMB = "(?:a{1500}){1500}"

MEASURE_BOMB = f"""
import resource
from tools.search_deadline import regex_deadline, regexp_search
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
try:
    with regex_deadline(5):
        regexp_search({BOMB!r}, "aaa")
except Exception:
    pass
print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024 - before)
"""


def cap_child_memory() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (1_500_000_000, 1_500_000_000))


def test_bomb_pattern_allocates_little() -> None:
    """Measured in a child process with a hard memory cap, so a failing run is safe."""
    result = subprocess.run(
        [sys.executable, "-I", "-c", MEASURE_BOMB],
        capture_output=True,
        text=True,
        timeout=60,
        preexec_fn=cap_child_memory,
    )
    assert int(result.stdout.strip()) < 100, result.stderr


def test_bomb_pattern_is_rejected() -> None:
    with sd.regex_deadline(5) as deadline:
        with pytest.raises(sd.SearchStopped) as stopped:
            sd.regexp_search(BOMB, "aaa")
        assert deadline.stopped is stopped.value
    assert (
        stopped.value.message
        == "That search pattern is too complex. Use a simpler pattern."
    )


def test_bomb_pattern_is_rejected_by_sub() -> None:
    with sd.regex_deadline(5):
        with pytest.raises(sd.SearchStopped):
            sd.sub(BOMB, "x", "aaa")


def test_over_long_pattern_is_rejected() -> None:
    with sd.regex_deadline(5):
        with pytest.raises(sd.SearchStopped) as stopped:
            sd.regexp_search("a" * 2001, "aaa")
    assert (
        stopped.value.message
        == "That search pattern is too complex. Use a simpler pattern."
    )


def test_deeply_nested_pattern_cannot_crash_the_search() -> None:
    """Whether Python allows 900 levels depends on the recursion limit at the
    time, which other code may change. Both outcomes are safe: the 2000
    character cap bounds the depth, so it either compiles or is refused."""
    with sd.regex_deadline(5):
        try:
            sd.regexp_search("(" * 900 + "a" + ")" * 900, "aaa")
        except sd.SearchStopped:
            pass


@pytest.mark.parametrize(
    "pattern",
    [
        "(?R)",
        "(?R)?",
        "(?0)*",
        "(a)(?1)*",
        "(a)(?-1)",
        "(?P<x>a)(?&x)*",
        "(?P<x>a)(?P>x)*",
        r"(?P<x>a)\g<x>*",
        "(?P<x>(?&x)a?)",
        "((?1))",
    ],
)
def test_recursion_is_rejected(pattern: str) -> None:
    """Recursion eats memory faster than the time budget can stop it."""
    with sd.regex_deadline(5):
        with pytest.raises(sd.SearchStopped) as stopped:
            sd.regexp_search(pattern, "aaa")
    assert (
        stopped.value.message
        == "That search pattern is too complex. Use a simpler pattern."
    )


@pytest.mark.parametrize("pattern", ["(", "*a", ")", "[a-"])
def test_invalid_pattern_gets_a_message(pattern: str) -> None:
    with sd.regex_deadline(5):
        with pytest.raises(sd.SearchStopped) as stopped:
            sd.regexp_search(pattern, "aaa")
    assert stopped.value.message == "That search pattern is not valid."


@pytest.mark.parametrize(
    "pattern",
    [
        "dhamma",
        r"\d{4}-\d{2}",
        "[a-z]{1,3}x",
        "(?:ab){1,50}",
        "^ nibbuto$",
        r"\p{L}+",
        r"\p{Lu}{2}",
        r"\p{Script=Latin}+",
        r"\d{1,3}\s{2,}",
        fuzzy_replace("dhammacakkappavattana"),
        fuzzy_replace("a" * 100),
    ],
)
def test_ordinary_patterns_are_accepted(pattern: str) -> None:
    with sd.regex_deadline(5):
        sd.regexp_search(pattern, "text")


def test_one_search_runs_and_the_next_waits_its_turn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Measured: alone a full scan takes 1.4 s; four at once took 17.8 s each,
    because they fight over Python's global lock. So they take turns."""
    monkeypatch.setattr(sd, "QUEUE_WAIT_SECONDS", 3.0)
    waiter_busy: list[bool] = []

    def waiter() -> None:
        with sd.regex_deadline(5) as deadline:
            waiter_busy.append(deadline.busy)

    with sd.regex_deadline(5) as first:
        assert first.busy is False
        thread = threading.Thread(target=waiter)
        thread.start()
        time.sleep(0.2)
        assert waiter_busy == []  # still waiting, not rejected
    thread.join()
    assert waiter_busy == [False]  # got its turn when the first finished


def test_a_search_that_waits_too_long_is_told_the_server_is_busy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sd, "QUEUE_WAIT_SECONDS", 0.3)
    with sd.regex_deadline(5):
        with sd.regex_deadline(5) as second:
            with pytest.raises(sd.SearchStopped) as stopped:
                sd.regexp_search("a", "a")
            assert second.stopped is stopped.value
    assert stopped.value.message == "The server is busy. Try again in a moment."


def test_a_full_queue_is_told_the_server_is_busy_at_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One running and three waiting fill the queue; the fifth does not wait."""
    monkeypatch.setattr(sd, "QUEUE_WAIT_SECONDS", 2.0)
    started = threading.Barrier(4)
    done = threading.Event()

    def wait_in_queue() -> None:
        started.wait()
        with sd.regex_deadline(5):
            done.wait(5)

    with sd.regex_deadline(5):
        threads = [threading.Thread(target=wait_in_queue) for _ in range(3)]
        for thread in threads:
            thread.start()
        started.wait()
        time.sleep(0.2)  # let the three reach the waiting line
        begun = time.monotonic()
        with sd.regex_deadline(5) as fifth:
            assert fifth.busy is True
        assert time.monotonic() - begun < 0.5
    done.set()
    for thread in threads:
        thread.join()
    with sd.regex_deadline(5) as after:
        assert after.busy is False


def test_a_stopped_search_is_raised_again_by_raise_if_stopped() -> None:
    with sd.regex_deadline(5):
        with pytest.raises(sd.SearchStopped):
            sd.regexp_search("(", "a")
        with pytest.raises(sd.SearchStopped):
            sd.raise_if_stopped()
    sd.raise_if_stopped()


def test_fuzzy_matching_is_stopped_by_the_time_budget_alone() -> None:
    """No rule for it: the worst fuzzy patterns measured stay near 32 MB, and
    the budget ends the slow ones."""
    start = time.monotonic()
    with sd.regex_deadline(0.5):
        with pytest.raises(sd.SearchTimeout):
            sd.regexp_search("(?:zzzzzzzzzzzzzzzzzzzz){i<=65000}", "dhamma " * 3000)
    assert time.monotonic() - start < 3
