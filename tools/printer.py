"""Utilities for colored console output with timing."""

from datetime import datetime
import time
from typing import ClassVar

from rich import print


class Printer:
    """Colored console output with timing."""

    def __init__(self) -> None:
        self.start_time: float | None = None

    # Class variable for main timer
    _ticx: ClassVar[datetime | None] = None

    @classmethod
    def tic(cls) -> None:
        """Start the main clock."""
        cls._ticx = datetime.now()

    @classmethod
    def toc(cls) -> None:
        """Stop the main clock and print elapsed time."""
        if cls._ticx is None:
            print("[red]Error: tic() not called before toc()[/red]")
            return

        tocx = datetime.now()
        tictoc = tocx - cls._ticx
        print("[cyan]" + ("-" * 40))
        print(f"[cyan]{tictoc}")
        print()

    def bip(self) -> None:
        """Start a mini clock."""
        self.start_time = time.time()

    def bop(self) -> str:
        """End mini clock and return elapsed time."""
        if self.start_time is None:
            return "0.000"
        elapsed_time = time.time() - self.start_time
        return f"{elapsed_time:.3f}"

    def print_bop(self) -> None:
        """Print the elapsed time right-aligned."""
        print(f"{self.bop():>10}")

    # Printer methods
    def yellow_title(self, text: str) -> None:
        """Print bright yellow title and start timer."""
        print(f"[bright_yellow]{text}")
        self.bip()

    def green_title(self, message: str) -> None:
        """Print green title and start timer."""
        print(f"[green]{message}")
        self.bip()

    def green_tmr(self, message: str) -> None:
        """Print left-aligned green message and start timer."""
        print(f"[green]{message:<35}", end="")
        self.bip()

    def cyan_tmr(self, message: str) -> None:
        """Print left-aligned cyan message and start timer."""
        print(f"[cyan]{message:<35}", end="")
        self.bip()

    def white_tmr(self, message: str) -> None:
        """Print indented white message and start timer."""
        print(f"{'':<5}[white]{message:<30}", end="")
        self.bip()

    def yes(self, message: int | str) -> None:
        """Print right-aligned blue message with timing."""
        if isinstance(message, int):
            formatted = f"{message:>10,}"
        else:
            formatted = f"{message:>10}"
        print(f"[blue]{formatted}", end="")
        self.print_bop()

    def no(self, message: int | str) -> None:
        """Print right-aligned red message with timing."""
        print(f"[red]{message:>10}", end="")
        self.print_bop()

    def counter(self, counter: int, total: int, word: str) -> None:
        """Print progress counter with timing."""
        print(f"{counter:>10,} / {total:<10,} {word[:20]:<20} {self.bop():>10}")
        self.bip()

    def summary(self, key: str, value: str | int) -> None:
        """Print key-value summary in green."""
        print(f"[green]{key:<20}[/green]{value}")

    # basic messages

    def red(self, message: str) -> None:
        """Print red message."""

        print(f"[red]{message}")

    def green(self, message: str) -> None:
        """Print green message."""

        print(f"[green]{message}")

    def amber(self, message: str) -> None:
        """Print amber message."""

        print(f"[yellow]{message}")

    def white(self, message: str) -> None:
        """Print white message."""

        print(f"[white]{message}")

    def cyan(self, message: str) -> None:
        """Print cyan message."""

        print(f"[cyan]{message}")


# Create singleton instance
printer = Printer()
