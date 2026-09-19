# Measurement harnesses

Two instrumented launchers. Both run the real editor — they monkeypatch
`gui2.main` for timing only and change no behaviour.

Run from the project root:

```bash
PYTHONPATH=. uv run .venv/bin/python3 \
  kamma/threads/20260918_gui2_startup_latency/artifacts/timed_gui.py
```

## `timed_gui.py`

Stamps: flet client connected, first paint (with `App.__init__` duration),
each tab as it is built, all tabs warmed, database loaded.

`NO_WARMUP=1` skips the warm-up entirely — the control for how long the
database load takes with nothing competing.

## `timed_gui2_deferred.py`

Adds a breakdown of `App.__init__` (toolkit vs `build_ui`, the remainder being
the deferred view imports), and holds the warm-up on an `Event` until the
database load finishes. This is the *proposed* Phase 3 behaviour, simulated
from outside, so the win could be measured before writing it.

Once Phase 3 lands, the real code does this and `timed_gui.py` alone is
enough.

## Reading the output

Only `[startup]` lines come from the harness. The uvicorn bind error and the
AI-provider lines are the app's normal noise — see the spec's "What's not
included".

Every figure must be a median of at least three runs on a warm page cache.
Single runs on this app vary by more than a second; the spec's original
baseline table was single runs and is flagged as such.
