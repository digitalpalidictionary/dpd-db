import re
from abc import ABC, abstractmethod

from bs4 import element


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
        self.sutta_counter = 0
        self.sutta_counter_alt = 0

        self.samyutta: str = ""
        self.samyutta_counter = 0
        self.anguttara_counter = 0
        self.vin_book: str = ""

        self.section = ""
        self.section_counter = 0
        self.section_counter_alt = 0

        self.vagga: str = ""
        self.vagga_counter = 0
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
