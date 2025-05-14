"""Utilities for colored console output with timing and structured TSV logging."""

import logging
from datetime import datetime
import time
from pathlib import Path
from rich import print
from typing import Union, Optional, ClassVar


class TSVFormatter(logging.Formatter):
    """Format log records as TSV with headers."""

    FIELDS = [
        "timestamp",
        "level",
        "operation",
        "type",  # title, status, success, error, etc
        "message",  # original message
        "elapsed",  # timing from bop()
        "count",  # for numerical outputs
        "session",  # to group related operations
    ]

    def __init__(self):
        super().__init__()
        self.header_written = False

    def format(self, record):
        # Write header on first use
        if not self.header_written:
            self.header_written = True
            return "\t".join(self.FIELDS)

        # Add extra fields to record
        for k, v in record.__dict__.get("extra", {}).items():
            setattr(record, k, v)

        # Extract values for each field
        values = []
        for field in self.FIELDS:
            if field == "timestamp":
                values.append(self.formatTime(record))
            elif field == "level":
                values.append(record.levelname)
            elif field == "message":
                values.append(record.getMessage())
            else:
                # Get fields from record attributes
                values.append(str(getattr(record, field, "")))

        return "\t".join(values)


class Printer:
    """Colored console output with timing and TSV logging."""

    def __init__(self, log_file: Optional[Path] = None):
        self.line = "-" * 40
        self.start_time: float | None = None
        self.session = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Set up logging if log_file provided
        self.logger = None
        if log_file:
            self.logger = logging.getLogger("dpd")
            self.logger.setLevel(logging.INFO)

            # File handler with TSV formatting
            handler = logging.FileHandler(log_file)
            handler.setFormatter(TSVFormatter())
            self.logger.addHandler(handler)

    def _log(self, level: int, operation: str, msg: str, **kwargs) -> None:
        """Log with additional context if logging is enabled."""
        if self.logger:
            # Create dictionary of extra fields
            extra = {"operation": operation, "session": self.session}

            # Add timing if available
            if self.start_time is not None:
                extra["elapsed"] = self.bop()

            # Add any additional kwargs
            extra.update(kwargs)

            # Log with extra fields
            self.logger.log(level, msg, extra=extra)

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
    def title(self, text: str) -> None:
        """Print bright yellow title and start timer."""
        print(f"[bright_yellow]{text}")
        self.bip()
        self._log(logging.INFO, "title", text, type="title")

    def green_title(self, message: str) -> None:
        """Print green title and start timer."""
        print(f"[green]{message}")
        self.bip()
        self._log(logging.INFO, "green_title", message, type="title")

    def green(self, message: str) -> None:
        """Print left-aligned green message and start timer."""
        print(f"[green]{message:<35}", end="")
        self.bip()
        self._log(logging.INFO, "status", message, type="status")

    def cyan(self, message: str) -> None:
        """Print left-aligned cyan message and start timer."""
        print(f"[cyan]{message:<35}", end="")
        self.bip()
        self._log(logging.INFO, "status", message, type="status")

    def white(self, message: str) -> None:
        """Print indented white message and start timer."""
        print(f"{'':<5}[white]{message:<30}", end="")
        self.bip()
        self._log(logging.INFO, "info", message, type="info")

    def yes(self, message: Union[int, str]) -> None:
        """Print right-aligned blue message with timing."""
        if isinstance(message, int):
            formatted = f"{message:>10,}"
            self._log(
                logging.INFO, "success", str(message), type="success", count=message
            )
        else:
            formatted = f"{message:>10}"
            self._log(logging.INFO, "success", message, type="success")
        print(f"[blue]{formatted}", end="")
        self.print_bop()

    def no(self, message: Union[int, str]) -> None:
        """Print right-aligned red message with timing."""
        print(f"[red]{message:>10}", end="")
        self.print_bop()
        self._log(logging.WARNING, "failure", str(message), type="failure")

    def red(self, message: str) -> None:
        """Print red message."""
        print(f"[red]{message}")
        self._log(logging.ERROR, "error", message, type="error")

    def counter(self, counter: int, total: int, word: str) -> None:
        """Print progress counter with timing."""
        print(f"{counter:>10,} / {total:<10,} {word[:20]:<20} {self.bop():>10}")
        self.bip()
        self._log(
            logging.INFO, "counter", word, type="progress", count=counter, total=total
        )

    def summary(self, key: str, value: str | int) -> None:
        """Print key-value summary in green."""
        print(f"[green]{key:<20}[/green]{value}")
        self._log(logging.INFO, "summary", f"{key}: {value}", type="summary", key=key)

    # basic logging messages

    def info(self, message: str) -> None:
        """Print green message."""

        print(f"[green]{message}")
        self._log(logging.INFO, "info", message, type="info")

    def warning(self, message: str) -> None:
        """Print amber message."""

        print(f"[yellow]{message}")
        self._log(logging.WARNING, "warning", message, type="warning")

    def error(self, message: str) -> None:
        """Print red message."""

        print(f"[red]{message}")
        self._log(logging.ERROR, "error", message, type="error")


# Create singleton instance with optional log file
printer = Printer(Path("dpd_operations.log"))
