""" Helper module to measure execution time
"""

import time

import rich

from typing import Optional


def close_line(stop_watch: 'StopWatch') -> None:
    rich.print('[cyan]' '-' * 40)
    rich.print(f'time: {stop_watch}')


class StopWatch:
    """ Measure execution time

    Examples:
        timer = StopWatch()
        some_job_1()
        timer.stop()
        some_job_2()
        print(timer)

    Equivalent example with a context manager:
        with StopWatch() as timer:
            some_job1()
        some_job_2()
        print(timer)
    """

    def __init__(self) -> None:
        self._start_time: float = time.time()
        self._duration: Optional[float] = None

    def stop(self) -> float:
        """ Stop counting, do not increment duration more """
        self._duration = self._get_delta()
        return self.duration

    @property
    def duration(self) -> float:
        """ Current counting duration in sec """
        if self._duration is None:
            return self._get_delta()
        return self._duration

    @property
    def duration_str(self) -> str:
        """ Nice formatted current duration """
        return self.format_duration(self.duration)

    @staticmethod
    def format_duration(duration: float) -> str:
        """ Format sec to "M min SS sec" form"""
        return f'{duration // 60:.0f} min {duration % 60:02.0f} sec'

    def _get_delta(self) -> float:
        return time.time() - self._start_time

    def __enter__(self) -> 'StopWatch':
        return self

    def __exit__(self, *args, **kwargs) -> None:
        self.stop()

    def __str__(self) -> str:
        return self.duration_str

    def __format__(self, format_spec: str) -> str:
        return format(self.duration_str, format_spec)
