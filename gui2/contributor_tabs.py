"""Which tabs a contributor-server user may see.

The tab decides what a contributor may do, not the user. The only per-user
setting is the list of extra tabs in DPD_GUI2_TABS."""

import logging
import os

BASE_TABS = ("Pass1Auto", "Pass1Add")
SAFE_TABS = ("Transl", "Bold Search")
READ_TABS = ("DB", "√", "Infl")

READ_ONLY_MESSAGE = "Read only: you can look but not save here."

logger = logging.getLogger(__name__)


def resolve_extra_tabs() -> list[str]:
    """Parse DPD_GUI2_TABS: comma-separated labels, blanks dropped."""
    raw = os.environ.get("DPD_GUI2_TABS", "")
    return [label.strip() for label in raw.split(",") if label.strip()]


def allowed_tabs(
    all_labels: list[str], extras: list[str]
) -> tuple[list[int], set[int]]:
    """Return the visible tab indices (in tab order) and the read-only indices.

    The indices are positions in all_labels, so every index-based lookup in
    gui2/main.py keeps its meaning. A hidden or unknown label is logged and
    dropped."""
    allowed: set[str] = set(BASE_TABS)
    for label in extras:
        if label in SAFE_TABS or label in READ_TABS:
            allowed.add(label)
        else:
            logger.warning("DPD_GUI2_TABS: ignoring hidden or unknown tab %r", label)

    visible = [i for i, label in enumerate(all_labels) if label in allowed]
    read_only = {i for i in visible if all_labels[i] in READ_TABS}
    return visible, read_only
