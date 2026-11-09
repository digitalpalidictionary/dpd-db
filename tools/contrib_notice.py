"""The notice file: how the nightly maintenance window tells open editors when it will stop them.

The window (`scripts/server_contrib/maintenance_window.py`) writes the stop time
here, and the gui2 editors read it. The format and the path live in this one
module so the writer and the reader cannot disagree. The file sits outside the
git tree so a pull or a rollback never touches it.
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

NOTICE_FILE: Path = Path("/var/lib/dpd/notice.json")

# A file left behind by a crashed window must not send a person who connects
# hours later to the offline page.
STALE_SECONDS = 60


def write_notice(path: Path, stop_at: datetime) -> None:
    """Write the stop time (aware UTC) by copy-and-replace, so a reader never sees half a file."""
    if stop_at.tzinfo is None or stop_at.utcoffset() != UTC.utcoffset(None):
        raise ValueError("stop_at must be a timezone-aware UTC datetime")
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps({"stop_at": stop_at.isoformat()}), encoding="utf-8")
    temp.chmod(0o644)
    os.replace(temp, path)


def read_notice(path: Path, now: datetime | None = None) -> tuple[datetime | None, str]:
    """Return `(stop_at, "ok")`, or `(None, reason)`. Never raises.

    Reasons: "absent", "unreadable", "bad time", "past".
    """
    now = now or datetime.now(UTC)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, "absent"
    except OSError:
        return None, "unreadable"
    try:
        data = json.loads(text)
    except ValueError:
        return None, "unreadable"
    if not isinstance(data, dict):
        return None, "unreadable"
    raw = data.get("stop_at")
    if not isinstance(raw, str):
        return None, "bad time"
    try:
        stop_at = datetime.fromisoformat(raw)
    except ValueError:
        return None, "bad time"
    if stop_at.tzinfo is None:
        return None, "bad time"
    if (now - stop_at).total_seconds() > STALE_SECONDS:
        return None, "past"
    return stop_at, "ok"


def remove_notice(path: Path) -> bool:
    """Delete the notice. Returns whether a file was there."""
    existed = path.exists()
    path.unlink(missing_ok=True)
    return existed
