import re
from abc import ABC, abstractmethod

from bs4 import element


def bump(value: str, step: int = 1) -> str:
    """Advance a counter by ``step``.

    Counters hold strings because a heading's number is often lifted verbatim from
    the text, and some are not numbers at all ('21-23', '(Paṭhamo bhāgo)', ''). Those
    are treated as zero rather than raising, which is what the old ``int`` counters
    did when they met a string: crash.
    """
    current = int(value) if value.lstrip("-").isdigit() else 0
    return str(current + step)


def is_counted(value: str) -> bool:
    """Whether a counter holds a real reference.

    Reproduces the truthiness of the former int counters, for which both 0 and "" meant
    "not set". Now that 0 is stored as "0", a plain truth test would read it as set.
    """
    return value not in ("", "0")


class BookParser(ABC):
    """Base class for per-book CST source/sutta parsers.

    Holds the mutable per-book parse state (counters, flags, current
    source/sutta) that used to live on ``GlobalData``. Subclasses declare which
    book codes they handle via ``books`` and carry the old per-book handler body
    in ``update()``, using ``self.*`` in place of ``g.*``. Counter seeds that
    used to live in ``init_sutta_counter`` / ``init_samyutta_counter`` move into
    each subclass ``__init__``.
    """

    books: tuple[str, ...] = ()

    def __init__(self, book: str) -> None:
        self.book: str = book

        self.source: str = ""
        self.source_alt: str = ""

        self.sutta: str = ""
        self.sutta_counter: str = "0"
        self.sutta_counter_alt = 0

        self.samyutta: str = ""
        self.samyutta_counter = 0
        self.anguttara_counter: str = "0"
        self.vin_book: str = ""

        self.section = ""
        self.section_counter: str = "0"
        self.section_counter_alt = 0

        self.vagga: str = ""
        self.vagga_counter: str = "0"
        self.vagga_alt_counter = 0

        self.subtitle_counter = 0

        self.is_api: bool = False
        self.is_bhikkhuni: bool = False
        self.is_abhinava: bool = False

    @property
    def sutta_clean(self):
        return re.sub(",.+", "", self.sutta)

    @abstractmethod
    def update(self, x: element.Tag) -> None:
        """Read the current chunk ``x`` and advance source/sutta/counters."""
        ...
