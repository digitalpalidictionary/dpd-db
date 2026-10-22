"""Limits for user-supplied regex searches in the webapp.

A route opens `regex_deadline()`. While it is open, the SQLite REGEXP callback
and `sub()` use the `regex` package, with a time budget, a pattern size guard
and a cap on how many searches run at once. Outside it (gui2, scripts)
nothing changes and plain `re` is used.
"""

import re
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import lru_cache
from typing import NoReturn

import regex
from sqlalchemy.orm import Session

# Seconds of the search's own CPU time. Searches take turns on Python's global
# lock, so wall time overstates the work: four ordinary full-table scans at
# once each wait about three times as long as they run, and a wall-clock
# budget failed all four at 4.00 s (measured). 4.0 is about 4x the slowest
# full-table scan on the real data (1.0 s of CPU).
SEARCH_BUDGET_SECONDS = 4.0
# Wall time is only a backstop, for a search stuck waiting (slow disk, a
# stalled client), which uses no CPU and so never spends the budget.
WALL_LIMIT_FACTOR = 5

# Regex searches take turns. Measured on the real data: one full scan costs
# 1.4 s alone, but two at once cost 3.8 s each, three 9.0 s and four 17.8 s,
# because the REGEXP callbacks fight over Python's global lock. One search
# runs at a time. Up to three more wait their turn, so a short burst of
# visitors is served. Beyond that, or after waiting this long, the visitor is
# told the server is busy. Waiting is capped so it cannot tie up the
# server's request threads.
MAX_RUNNING_SEARCHES = 1
MAX_WAITING_SEARCHES = 3
QUEUE_WAIT_SECONDS = 10.0

# The regex package expands a counted repeat when it compiles: (?:a{3000}){3000}
# is 17 characters and needs 2.4 GB, where `re` needs almost nothing. Memory
# grows with pattern length x the product of all counts, so that is capped.
# 100,000 compiles in ~30 MB. 2000 characters fit a fuzzy-expanded 100-letter word.
MAX_PATTERN_CHARS = 2000
MAX_PATTERN_COST = 100_000

TIMEOUT_MESSAGE = "The search took too long. Use a more specific search."
BUSY_MESSAGE = "The server is busy. Try again in a moment."
TOO_COMPLEX_MESSAGE = "That search pattern is too complex. Use a simpler pattern."
INVALID_MESSAGE = "That search pattern is not valid."


class SearchStopped(Exception):
    """A search that ended on purpose. `message` is safe to show the user."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SearchTimeout(SearchStopped):
    def __init__(self) -> None:
        super().__init__(TIMEOUT_MESSAGE)


class SearchBusy(SearchStopped):
    def __init__(self) -> None:
        super().__init__(BUSY_MESSAGE)


class PatternRejected(SearchStopped):
    pass


@dataclass
class Deadline:
    cpu_ends_at: float
    wall_ends_at: float
    busy: bool = False
    # SQLite wraps an error raised inside REGEXP in its own OperationalError,
    # so callers read this to tell a stopped search from a real database error.
    stopped: SearchStopped | None = None

    def stop(self, reason: SearchStopped) -> NoReturn:
        self.stopped = reason
        raise reason

    def remaining(self) -> float:
        if self.busy:
            self.stop(SearchBusy())
        left = min(
            self.cpu_ends_at - time.thread_time(),
            self.wall_ends_at - time.monotonic(),
        )
        if left <= 0:
            self.stop(SearchTimeout())
        return left


_current: ContextVar[Deadline | None] = ContextVar("search_deadline", default=None)
_in_line = threading.BoundedSemaphore(MAX_RUNNING_SEARCHES + MAX_WAITING_SEARCHES)
_running = threading.BoundedSemaphore(MAX_RUNNING_SEARCHES)

_COUNT = re.compile(r"\{(\d*)(?:,(\d*))?\}")

# Recursion and group calls of the regex package ((?R) (?1) (?&x) \g<x>) use
# hundreds of MB in half a second while matching, so the time budget cannot
# stop them. Measured: (?R) and ((?1)) hit a 1.2 GB cap in 0.5 s. `re` has no
# such feature and a dictionary search has no use for it. Fuzzy matching
# ({e<=2}) needs no rule: its worst cases ran at 32 MB until the budget ended.
_RECURSION = re.compile(r"\(\?(?:R|[+-]?\d+|&\w+|P>\w+)\)|\\g<")


@contextmanager
def regex_deadline(seconds: float = SEARCH_BUDGET_SECONDS) -> Generator[Deadline]:
    in_line = _in_line.acquire(blocking=False)
    running = in_line and _running.acquire(timeout=QUEUE_WAIT_SECONDS)
    # the budget starts after the wait: waiting uses none of it.
    # thread_time: the route and its REGEXP callbacks run on one worker thread
    deadline = Deadline(
        cpu_ends_at=time.thread_time() + seconds,
        wall_ends_at=time.monotonic() + seconds * WALL_LIMIT_FACTOR,
        busy=not running,
    )
    token = _current.set(deadline)
    try:
        yield deadline
    finally:
        _current.reset(token)
        if running:
            _running.release()
        if in_line:
            _in_line.release()


def current_deadline() -> Deadline | None:
    return _current.get()


def raise_if_stopped() -> None:
    """Re-raise a stop that a catch-all `except` block just swallowed."""
    deadline = _current.get()
    if deadline is not None and deadline.stopped is not None:
        raise deadline.stopped


def _check_pattern(expr: str) -> None:
    if len(expr) > MAX_PATTERN_CHARS or _RECURSION.search(expr):
        raise PatternRejected(TOO_COMPLEX_MESSAGE)
    cost = len(expr)
    for low, high in _COUNT.findall(expr):
        cost *= max(int(low or 0), int(high or 0), 1)
        if cost > MAX_PATTERN_COST:
            raise PatternRejected(TOO_COMPLEX_MESSAGE)


@lru_cache(maxsize=4)
def _compile(expr: str) -> "regex.Pattern[str]":
    """SQLite calls REGEXP once per row. regex.search re-resolves the pattern
    each call, which made a full scan 3-6x slower than `re`."""
    _check_pattern(expr)
    try:
        return regex.compile(expr)
    except (MemoryError, RecursionError, OverflowError):
        raise PatternRejected(TOO_COMPLEX_MESSAGE) from None
    except regex.error:
        raise PatternRejected(INVALID_MESSAGE) from None


def _compiled(deadline: Deadline, expr: str) -> "regex.Pattern[str]":
    deadline.remaining()
    try:
        return _compile(expr)
    except PatternRejected as rejected:
        deadline.stop(rejected)


def regexp_search(expr: str, item: str | None) -> bool | None:
    """SQLite REGEXP, limited inside a deadline.

    Outside a deadline it matches SQLAlchemy's own sqlite REGEXP exactly
    (case-sensitive, NULL in gives NULL out), which is what runs today.
    """
    if item is None:
        return None
    deadline = _current.get()
    if deadline is None:
        return re.search(expr, item) is not None
    pattern = _compiled(deadline, expr)
    try:
        # concurrent=True releases the GIL, so a slow pattern cannot starve
        # other requests while it runs. regex times one call by process CPU
        # time, not this thread's, so with other threads busy a single runaway
        # match can stop sooner than the budget (measured: 0.55 s instead of
        # 3.3 s under 8 heavy lookups). Ordinary row matches take microseconds
        # and are not affected.
        return (
            pattern.search(item, timeout=deadline.remaining(), concurrent=True)
            is not None
        )
    except TimeoutError:
        deadline.stop(SearchTimeout())


def install_regexp(session: Session) -> None:
    """Put the deadline-aware REGEXP on this session's connection.

    SQLAlchemy's sqlite dialect registers its own REGEXP when the connection
    opens, and it wins over an engine-wide listener, so it is replaced here.
    """
    raw = session.connection().connection.driver_connection
    if raw is None:
        raise RuntimeError("session has no open sqlite connection")
    raw.create_function("REGEXP", 2, regexp_search)


def sub(pattern: str, repl: str, string: str) -> str:
    """`re.sub`, limited inside a deadline."""
    deadline = _current.get()
    if deadline is None:
        return re.sub(pattern, repl, string)
    compiled = _compiled(deadline, pattern)
    try:
        return compiled.sub(repl, string, timeout=deadline.remaining(), concurrent=True)
    except TimeoutError:
        deadline.stop(SearchTimeout())
