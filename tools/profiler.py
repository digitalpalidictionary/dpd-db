import rich
import tracemalloc


class MemoryProfiler:
    """ Context manager prints memory usage of most consuming modules

    Some module may have significantly higher consumption just because of some
    shared structure decided in its heap

    It has perfomance kick
    """
    def __init__(self, limit=15) -> None:
        self.limit = limit

    def __enter__(self) -> 'MemoryProfiler':
        tracemalloc.start()
        return self

    def __exit__(self, *args, **kwargs) -> None:
        statistics = tracemalloc.take_snapshot().statistics('lineno')
        rich.print('[yellow]' + '=' * 40)
        for stat in statistics[:self.limit]:
            rich.print(stat)
