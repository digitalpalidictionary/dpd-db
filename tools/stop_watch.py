""" Helper module to measure execution time
"""

import time

import rich
import rich.markup

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
        """ Format sec to human readable string """
        return f'{duration:06.3f} sec'

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


class Tic:
    """ Formatted output of stage and execution time """
    TEXT_WIDTH = 50
    TIME_WIDTH = 14
    ELLIPSIS = '...'
    TEMPLATE = '[green]{text:{text_width}}[/green]{time:{time_width}}'

    def __init__(self, text: str) -> None:
        self._active = True
        self.text = rich.markup.escape(text)
        self.timer = StopWatch()
        formatted_text = self.TEMPLATE.format(
            text=self.text, text_width=self.TEXT_WIDTH, time=self.ELLIPSIS, time_width=self.TIME_WIDTH)
        rich.print(formatted_text, end='\r')

    def __del__(self) -> None:
        if self._active:
            rich.print(f'[yellow bold]WARNING: {self.__class__.__name__} "{self.text}" unclosed')

    def __enter__(self) -> 'Tic':
        return self

    def __exit__(self, *args, **kwargs) -> None:
        self.toc()

    def toc(self) -> None:
        if not self._active:
            rich.print(f'[yellow bold]WARNING: closing {self.__class__.__name__} "{self.text}", but already closed')
        formatted_text = self.TEMPLATE.format(
            text=self.text, text_width=self.TEXT_WIDTH, time=self.timer, time_width=self.TIME_WIDTH)
        rich.print(formatted_text)
        self._active = False
